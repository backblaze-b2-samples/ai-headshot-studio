"""Local, REAL Stable-Diffusion-1.5 LoRA fine-tuning via diffusers + peft.

This is the default trainer. It genuinely fine-tunes a LoRA on the subject's
selfies — no simulation. The heavy ML stack (torch / diffusers / transformers
/ peft) is imported lazily *inside* the methods so the rest of the app and
`pnpm dev` stay light and import-clean.

Tradeoff: SD-class quality and slow-on-CPU speed (GPU/MPS recommended). The
output is a standard PEFT/diffusers LoRA `.safetensors` written to B2.
"""

import io
import logging
import tempfile
from pathlib import Path

from app.repo.b2_client import put_bytes
from app.repo.subjects_store import lora_key
from app.repo.trainer.base import ProgressFn, Trainer, TrainRequest, TrainResult

logger = logging.getLogger(__name__)


def _pick_device():
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class LocalTrainer(Trainer):
    name = "local"

    def __init__(self, base_model: str):
        self.base_model = base_model

    def train(self, req: TrainRequest, on_progress: ProgressFn) -> TrainResult:
        # --- lazy heavy imports (contained to this adapter) ---
        import torch
        from diffusers import (
            AutoencoderKL,
            DDPMScheduler,
            StableDiffusionPipeline,
            UNet2DConditionModel,
        )
        from diffusers.utils import convert_state_dict_to_diffusers
        from peft import LoraConfig
        from peft.utils import get_peft_model_state_dict
        from PIL import Image
        from transformers import CLIPTextModel, CLIPTokenizer

        device = _pick_device()
        logger.info(
            "Local LoRA training: subject=%s device=%s steps=%d samples=%d",
            req.subject_id, device, req.steps, len(req.samples),
        )

        tokenizer = CLIPTokenizer.from_pretrained(
            self.base_model, subfolder="tokenizer"
        )
        text_encoder = CLIPTextModel.from_pretrained(
            self.base_model, subfolder="text_encoder"
        ).to(device)
        vae = AutoencoderKL.from_pretrained(
            self.base_model, subfolder="vae"
        ).to(device)
        unet = UNet2DConditionModel.from_pretrained(
            self.base_model, subfolder="unet"
        ).to(device)
        noise_scheduler = DDPMScheduler.from_pretrained(
            self.base_model, subfolder="scheduler"
        )

        # Freeze the base; train only the injected LoRA layers on the UNet.
        vae.requires_grad_(False)
        text_encoder.requires_grad_(False)
        unet.requires_grad_(False)

        unet.add_adapter(
            LoraConfig(
                r=req.lora_rank,
                lora_alpha=req.lora_rank,
                init_lora_weights="gaussian",
                target_modules=["to_k", "to_q", "to_v", "to_out.0"],
            )
        )
        lora_params = [p for p in unet.parameters() if p.requires_grad]
        optimizer = torch.optim.AdamW(lora_params, lr=req.learning_rate)

        # Pre-encode the captioned selfies into latents + text embeddings.
        examples = self._prepare_examples(
            req, device, Image, tokenizer, text_encoder, vae, torch
        )
        if not examples:
            raise RuntimeError("No usable training selfies after decoding")

        unet.train()
        on_progress(0, req.steps)
        for step in range(req.steps):
            ex = examples[step % len(examples)]
            latents = ex["latents"]
            noise = torch.randn_like(latents)
            timesteps = torch.randint(
                0, noise_scheduler.config.num_train_timesteps,
                (latents.shape[0],), device=device,
            ).long()
            noisy = noise_scheduler.add_noise(latents, noise, timesteps)
            pred = unet(noisy, timesteps, ex["text_embeds"]).sample
            target = (
                noise if noise_scheduler.config.prediction_type == "epsilon"
                else noise_scheduler.get_velocity(latents, noise, timesteps)
            )
            loss = torch.nn.functional.mse_loss(pred.float(), target.float())
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            on_progress(step + 1, req.steps)

        key = self._save_lora(
            unet, StableDiffusionPipeline, get_peft_model_state_dict,
            convert_state_dict_to_diffusers, req.subject_id,
        )
        return TrainResult(lora_key=key, steps_done=req.steps)

    def _prepare_examples(self, req, device, Image, tokenizer, text_encoder, vae, torch):
        examples = []
        with torch.no_grad():
            for s in req.samples:
                try:
                    img = Image.open(io.BytesIO(s.image_bytes)).convert("RGB")
                except Exception:
                    logger.warning("Skipping undecodable selfie in subject=%s", req.subject_id)
                    continue
                img = img.resize((req.resolution, req.resolution))
                arr = torch.tensor(
                    list(img.tobytes()), dtype=torch.float32
                ).reshape(req.resolution, req.resolution, 3)
                arr = (arr / 127.5 - 1.0).permute(2, 0, 1).unsqueeze(0).to(device)
                latents = vae.encode(arr).latent_dist.sample()
                latents = latents * vae.config.scaling_factor

                prompt = s.caption or f"a photo of {req.trigger_token}"
                tokens = tokenizer(
                    prompt, padding="max_length",
                    max_length=tokenizer.model_max_length,
                    truncation=True, return_tensors="pt",
                ).input_ids.to(device)
                text_embeds = text_encoder(tokens)[0]
                examples.append({"latents": latents, "text_embeds": text_embeds})
        return examples

    def _save_lora(self, unet, PipelineCls, get_state, convert, subject_id):
        state = convert(get_state(unet))
        with tempfile.TemporaryDirectory() as tmp:
            PipelineCls.save_lora_weights(
                save_directory=tmp,
                unet_lora_layers=state,
                safe_serialization=True,
            )
            files = list(Path(tmp).glob("*.safetensors"))
            if not files:
                raise RuntimeError("LoRA save produced no .safetensors file")
            data = files[0].read_bytes()
        key = lora_key(subject_id)
        put_bytes(key, data, "application/octet-stream")
        logger.info("Saved LoRA %s (%d bytes) for subject=%s", key, len(data), subject_id)
        return key

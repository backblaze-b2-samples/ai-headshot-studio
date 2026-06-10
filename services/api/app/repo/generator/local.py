"""Local, REAL headshot generation from the trained LoRA via diffusers.

Default generator. Loads the subject's likeness LoRA onto SD-1.5 and renders
genuine PNGs — no simulation. Heavy ML imports are lazy and contained here.
The loaded pipeline is cached per LoRA key so a multi-style run doesn't reload
weights for every image.
"""

import io
import logging
import tempfile
from pathlib import Path

from app.repo.b2_client import get_bytes, put_bytes
from app.repo.generator.base import (
    GeneratedImage,
    GenerateImageRequest,
    Generator,
)
from app.repo.subjects_store import headshot_key

logger = logging.getLogger(__name__)


def _pick_device():
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class LocalGenerator(Generator):
    name = "local"

    def __init__(self, base_model: str, steps: int, guidance: float, lora_scale: float):
        self.base_model = base_model
        self.steps = steps
        self.guidance = guidance
        self.lora_scale = lora_scale
        self._pipe = None
        self._loaded_lora: str | None = None

    def _pipeline(self, lora_key: str):
        if self._pipe is not None and self._loaded_lora == lora_key:
            return self._pipe
        import torch
        from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

        device = _pick_device()
        pipe = StableDiffusionPipeline.from_pretrained(
            self.base_model,
            safety_checker=None,
            torch_dtype=torch.float32,
        ).to(device)
        # DPM++ 2M Karras renders noticeably sharper, cleaner faces than the
        # SD-1.5 default sampler at the same step count.
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config,
            use_karras_sigmas=True,
            algorithm_type="dpmsolver++",
        )

        data = get_bytes(lora_key)
        if data is None:
            raise RuntimeError(f"LoRA weights missing at '{lora_key}'")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lora.safetensors"
            path.write_bytes(data)
            pipe.load_lora_weights(tmp, weight_name="lora.safetensors")
        pipe.set_progress_bar_config(disable=True)
        self._pipe = pipe
        self._loaded_lora = lora_key
        return pipe

    def generate(self, req: GenerateImageRequest, on_image) -> list[GeneratedImage]:
        import torch

        pipe = self._pipeline(req.lora_key)
        device = _pick_device()
        results: list[GeneratedImage] = []
        logger.info(
            "Local generation: subject=%s style=%s count=%d",
            req.subject_id, req.style_slug, req.count,
        )
        for i in range(req.count):
            idx = req.start_index + i
            generator = torch.Generator(device=device).manual_seed(
                hash((req.subject_id, req.style_slug, idx)) % (2**31)
            )
            image = pipe(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt,
                num_inference_steps=req.steps,
                guidance_scale=req.guidance,
                cross_attention_kwargs={"scale": self.lora_scale},
                generator=generator,
            ).images[0]
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            key = headshot_key(req.subject_id, req.style_slug, idx)
            put_bytes(key, buf.getvalue(), "image/png")
            out = GeneratedImage(key=key, style_slug=req.style_slug, index=idx)
            results.append(out)
            on_image(out)
        return results

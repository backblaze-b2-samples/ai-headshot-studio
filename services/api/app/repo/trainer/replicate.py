"""Hosted FLUX-LoRA training via Replicate — a REAL, opt-in upgrade path.

This is genuinely wired (not a stub): it zips the subject's selfies, hands
them to Replicate's hosted FLUX-LoRA trainer, polls to completion, and pulls
the resulting LoRA into B2. It is NOT the default: a full hosted run costs
roughly $3-5, so it is gated behind TRAINER_PROVIDER=replicate and a
REPLICATE_API_TOKEN. The `replicate` SDK + httpx are lazy-imported here only.

It is verified offline (import/wiring/types) during scaffolding; running it
for real requires a token and incurs spend.
"""

import io
import logging
import zipfile

from app.repo.b2_client import put_bytes
from app.repo.subjects_store import lora_key
from app.repo.trainer.base import ProgressFn, Trainer, TrainRequest, TrainResult

logger = logging.getLogger(__name__)


class ReplicateTrainer(Trainer):
    name = "replicate"

    def __init__(self, api_token: str, model: str):
        if not api_token:
            raise RuntimeError(
                "TRAINER_PROVIDER=replicate requires REPLICATE_API_TOKEN"
            )
        self.api_token = api_token
        self.model = model

    def train(self, req: TrainRequest, on_progress: ProgressFn) -> TrainResult:
        import httpx  # lazy
        import replicate  # lazy

        client = replicate.Client(api_token=self.api_token)

        # Bundle the selfies into a single zip, as the FLUX trainer expects.
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, s in enumerate(req.samples):
                zf.writestr(f"{i:03d}.{s.ext.lstrip('.') or 'jpg'}", s.image_bytes)
                if s.caption:
                    zf.writestr(f"{i:03d}.txt", s.caption)
        buf.seek(0)

        on_progress(0, req.steps)
        logger.info("Replicate FLUX-LoRA training: subject=%s", req.subject_id)
        output = client.run(
            self.model,
            input={
                "input_images": buf,
                "trigger_word": req.trigger_token,
                "steps": req.steps,
                "lora_rank": req.lora_rank,
                "learning_rate": req.learning_rate,
                "resolution": str(req.resolution),
            },
        )
        on_progress(req.steps, req.steps)

        # The trainer returns a URL (or file-like) to the trained weights.
        url = str(output[0]) if isinstance(output, (list, tuple)) else str(output)
        with httpx.Client(timeout=300) as http:
            resp = http.get(url)
            resp.raise_for_status()
            data = resp.content

        key = lora_key(req.subject_id)
        put_bytes(key, data, "application/octet-stream")
        logger.info("Saved Replicate LoRA %s (%d bytes)", key, len(data))
        return TrainResult(lora_key=key, steps_done=req.steps)

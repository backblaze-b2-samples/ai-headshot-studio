"""Hosted FLUX headshot generation via Replicate — REAL, opt-in path.

Genuinely wired (not a stub): runs the hosted FLUX-LoRA model with the
subject's trained LoRA and downloads each rendered image into B2. Gated behind
GENERATOR_PROVIDER=replicate + a REPLICATE_API_TOKEN because it costs money.
The `replicate` SDK + httpx are lazy-imported here only. Verified offline
during scaffolding.
"""

import logging

from app.repo.b2_client import get_presigned_url, put_bytes
from app.repo.generator.base import (
    GeneratedImage,
    GenerateImageRequest,
    Generator,
)
from app.repo.subjects_store import headshot_key

logger = logging.getLogger(__name__)


class ReplicateGenerator(Generator):
    name = "replicate"

    def __init__(self, api_token: str, model: str):
        if not api_token:
            raise RuntimeError(
                "GENERATOR_PROVIDER=replicate requires REPLICATE_API_TOKEN"
            )
        self.api_token = api_token
        self.model = model

    def generate(self, req: GenerateImageRequest, on_image) -> list[GeneratedImage]:
        import httpx  # lazy
        import replicate  # lazy

        client = replicate.Client(api_token=self.api_token)
        # The trained LoRA lives in B2; hand the hosted model a short-lived
        # presigned URL so it can fetch the weights.
        lora_url = get_presigned_url(req.lora_key, expires_in=900)
        results: list[GeneratedImage] = []
        logger.info(
            "Replicate generation: subject=%s style=%s count=%d",
            req.subject_id, req.style_slug, req.count,
        )
        with httpx.Client(timeout=300) as http:
            for i in range(req.count):
                idx = req.start_index + i
                output = client.run(
                    self.model,
                    input={
                        "prompt": req.prompt,
                        "lora_weights": lora_url,
                        "num_inference_steps": req.steps,
                        "guidance_scale": req.guidance,
                        "num_outputs": 1,
                    },
                )
                url = str(output[0]) if isinstance(output, (list, tuple)) else str(output)
                resp = http.get(url)
                resp.raise_for_status()
                key = headshot_key(req.subject_id, req.style_slug, idx)
                put_bytes(key, resp.content, "image/png")
                out = GeneratedImage(key=key, style_slug=req.style_slug, index=idx)
                results.append(out)
                on_image(out)
        return results

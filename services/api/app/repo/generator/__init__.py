"""Generator dispatcher.

`get_generator()` returns the configured generator. The default is the local,
real diffusers generator ($0, no keys). There is no simulated generator —
every headshot is a genuine model render.
"""

from app.config import settings
from app.repo.generator.base import (
    GeneratedImage,
    GenerateImageRequest,
    Generator,
    ProgressFn,
)

__all__ = [
    "GenerateImageRequest",
    "GeneratedImage",
    "Generator",
    "ProgressFn",
    "get_generator",
]


def get_generator() -> Generator:
    provider = settings.generator_provider.lower()
    if provider == "replicate":
        from app.repo.generator.replicate import ReplicateGenerator

        return ReplicateGenerator(
            api_token=settings.replicate_api_token,
            model=settings.replicate_generate_model,
        )
    if provider == "local":
        from app.repo.generator.local import LocalGenerator

        return LocalGenerator(
            base_model=settings.base_model,
            steps=settings.generate_steps,
            guidance=settings.generate_guidance,
        )
    raise RuntimeError(
        f"Unknown GENERATOR_PROVIDER '{settings.generator_provider}'. "
        "Use 'local' (default) or 'replicate'."
    )

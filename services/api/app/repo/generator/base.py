"""Generator interface shared by the local and Replicate adapters.

A generator loads the trained likeness LoRA and renders real headshot PNGs
for a given prompt, persisting each to B2 at
`subjects/{id}/headshots/{style_slug}/{NN}.png`. Every headshot in the gallery
is a genuine model output — there is no simulated generator.
"""

from collections.abc import Callable
from dataclasses import dataclass

# (images_done, images_total) -> None
ProgressFn = Callable[[int, int], None]


@dataclass
class GenerateImageRequest:
    subject_id: str
    lora_key: str
    trigger_token: str
    style_slug: str
    prompt: str
    negative_prompt: str
    count: int
    steps: int
    guidance: float
    start_index: int


@dataclass
class GeneratedImage:
    key: str
    style_slug: str
    index: int


class Generator:
    """Abstract generator. Implementations live in local.py / replicate.py."""

    name: str = "base"

    def generate(
        self,
        req: GenerateImageRequest,
        on_image: Callable[[GeneratedImage], None],
    ) -> list[GeneratedImage]:  # pragma: no cover - interface
        raise NotImplementedError

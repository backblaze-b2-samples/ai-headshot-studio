"""Trainer interface shared by the local and Replicate adapters.

A trainer takes a subject's captioned selfies and produces a likeness LoRA,
persisted to B2 at `subjects/{id}/model/{id}.safetensors`. Progress is reported
through a callback so the service layer can write it into the manifest, which
the frontend polls. Neither adapter simulates — the local adapter really
fine-tunes SD-1.5 with diffusers+peft, the Replicate adapter really calls the
hosted FLUX-LoRA trainer.
"""

from collections.abc import Callable
from dataclasses import dataclass

# (steps_done, steps_total) -> None
ProgressFn = Callable[[int, int], None]


@dataclass
class TrainSample:
    """One training example: the raw image bytes plus its caption."""

    image_bytes: bytes
    caption: str
    ext: str


@dataclass
class TrainRequest:
    subject_id: str
    trigger_token: str
    samples: list[TrainSample]
    steps: int
    resolution: int
    lora_rank: int
    learning_rate: float


@dataclass
class TrainResult:
    """Where the trained LoRA landed on B2 and how many steps actually ran."""

    lora_key: str
    steps_done: int


class Trainer:
    """Abstract trainer. Implementations live in local.py / replicate.py."""

    name: str = "base"

    def train(
        self, req: TrainRequest, on_progress: ProgressFn
    ) -> TrainResult:  # pragma: no cover - interface
        raise NotImplementedError

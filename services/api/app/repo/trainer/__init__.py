"""Trainer dispatcher.

`get_trainer()` returns the configured trainer. The default is the local,
real diffusers+peft SD-1.5 trainer ($0, no keys). There is no simulated
trainer — every LoRA is genuinely fit on the subject's selfies.
"""

from app.config import settings
from app.repo.trainer.base import (
    ProgressFn,
    Trainer,
    TrainRequest,
    TrainResult,
    TrainSample,
)

__all__ = [
    "ProgressFn",
    "TrainRequest",
    "TrainResult",
    "TrainSample",
    "Trainer",
    "get_trainer",
]


def get_trainer() -> Trainer:
    provider = settings.trainer_provider.lower()
    if provider == "replicate":
        from app.repo.trainer.replicate import ReplicateTrainer

        return ReplicateTrainer(
            api_token=settings.replicate_api_token,
            model=settings.replicate_train_model,
        )
    if provider == "local":
        from app.repo.trainer.local import LocalTrainer

        return LocalTrainer(base_model=settings.base_model)
    raise RuntimeError(
        f"Unknown TRAINER_PROVIDER '{settings.trainer_provider}'. "
        "Use 'local' (default) or 'replicate'."
    )

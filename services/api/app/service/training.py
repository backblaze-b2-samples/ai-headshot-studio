"""Training job orchestration.

Runs as a FastAPI BackgroundTask. The subject's manifest on B2 is the single
source of truth for progress — the trainer's progress callback writes
`train_steps_done` into it (throttled), and the frontend polls. No DB, no
in-memory job store. The real trainer (local diffusers+peft by default) does
the work; this layer only wires inputs, status, and progress.
"""

import logging

from app.config import settings
from app.repo import get_bytes
from app.repo.subjects_store import load_manifest, save_manifest
from app.repo.trainer import TrainRequest, TrainSample, get_trainer
from app.service.subjects import SubjectError, get_subject
from app.types.subject import Subject, SubjectStatus

logger = logging.getLogger(__name__)


def effective_train_steps(n_selfies: int) -> int:
    """Resolve the training step budget.

    A pinned ``train_steps > 0`` always wins (handy for fast smoke tests).
    Otherwise scale with the selfie count (~``train_steps_per_image`` each)
    and clamp to ``[train_steps_min, train_steps_max]`` so small sets aren't
    under-trained and large ones don't run forever on CPU/MPS.
    """
    if settings.train_steps > 0:
        return settings.train_steps
    target = settings.train_steps_per_image * max(n_selfies, 1)
    return max(settings.train_steps_min, min(target, settings.train_steps_max))


def start_training(subject_id: str) -> Subject:
    """Validate and flip the subject into TRAINING. Caller schedules run_training."""
    subject = get_subject(subject_id)
    if len(subject.selfies) < settings.min_selfies:
        raise SubjectError(
            f"Need at least {settings.min_selfies} selfies to train "
            f"(have {len(subject.selfies)})"
        )
    if subject.status in (SubjectStatus.TRAINING, SubjectStatus.GENERATING):
        raise SubjectError("A job is already running for this subject", 409)
    subject.status = SubjectStatus.TRAINING
    subject.train_steps_total = effective_train_steps(len(subject.selfies))
    subject.train_steps_done = 0
    subject.error = None
    save_manifest(subject)
    return subject


def run_training(subject_id: str) -> None:
    """Background entrypoint — performs the REAL fine-tune."""
    subject = load_manifest(subject_id)
    if subject is None:
        logger.error("run_training: subject %s vanished", subject_id)
        return
    try:
        samples: list[TrainSample] = []
        for ref in subject.selfies:
            data = get_bytes(ref.key)
            if data is None:
                continue
            ext = ref.key.rsplit(".", 1)[-1]
            caption = ref.caption or f"{subject.trigger_token}, a person"
            samples.append(TrainSample(image_bytes=data, caption=caption, ext=ext))
        if not samples:
            raise RuntimeError("No selfies available to train on")

        trainer = get_trainer()
        last_pct = {"v": -1}

        def on_progress(done: int, total: int) -> None:
            # Throttle manifest writes to whole-percent changes to keep B2
            # PUTs bounded even for long runs.
            pct = int(done / total * 100) if total else 0
            if pct != last_pct["v"]:
                last_pct["v"] = pct
                subject.train_steps_done = done
                subject.train_steps_total = total
                save_manifest(subject)

        result = trainer.train(
            TrainRequest(
                subject_id=subject.id,
                trigger_token=subject.trigger_token,
                samples=samples,
                steps=effective_train_steps(len(samples)),
                resolution=settings.train_resolution,
                lora_rank=settings.train_lora_rank,
                learning_rate=settings.train_learning_rate,
            ),
            on_progress,
        )
        subject.lora_key = result.lora_key
        subject.train_steps_done = result.steps_done
        subject.status = SubjectStatus.TRAINED
        subject.error = None
        save_manifest(subject)
        logger.info("Training complete: subject=%s lora=%s", subject_id, result.lora_key)
    except Exception as e:
        logger.error("Training failed: subject=%s err=%s", subject_id, e, exc_info=True)
        subject.status = SubjectStatus.FAILED
        subject.error = f"Training failed: {e}"
        save_manifest(subject)

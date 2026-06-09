from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SubjectStatus(StrEnum):
    """Lifecycle of a subject. The manifest's status is the single source of
    truth — the frontend polls it while a job is in flight."""

    CREATED = "created"          # selfies being uploaded
    CAPTIONING = "captioning"    # auto-captioning selfies
    READY_TO_TRAIN = "ready_to_train"
    TRAINING = "training"        # LoRA fine-tuning in progress
    TRAINED = "trained"          # LoRA ready, can generate
    GENERATING = "generating"    # rendering headshots across style packs
    COMPLETE = "complete"        # at least one headshot generated
    FAILED = "failed"


class SelfieRef(BaseModel):
    image_id: str
    key: str
    filename: str
    caption: str | None = None


class HeadshotRef(BaseModel):
    style_slug: str
    key: str
    index: int


class Subject(BaseModel):
    """Manifest persisted at subjects/{id}/subject.json — system of record."""

    id: str
    name: str
    status: SubjectStatus = SubjectStatus.CREATED
    created_at: datetime
    updated_at: datetime

    trigger_token: str  # the rare token the LoRA binds the likeness to
    trainer_provider: str = "local"
    generator_provider: str = "local"

    selfies: list[SelfieRef] = Field(default_factory=list)
    styles_requested: list[str] = Field(default_factory=list)
    headshots: list[HeadshotRef] = Field(default_factory=list)

    lora_key: str | None = None
    train_steps_done: int = 0
    train_steps_total: int = 0
    headshots_done: int = 0
    headshots_total: int = 0

    error: str | None = None


class SubjectSummary(BaseModel):
    """Lightweight row for the /gallery subject list."""

    id: str
    name: str
    status: SubjectStatus
    created_at: datetime
    updated_at: datetime
    selfie_count: int
    headshot_count: int
    cover_key: str | None = None


class CreateSubjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class GenerateRequest(BaseModel):
    style_slugs: list[str] = Field(min_length=1)

"""System of record for subjects.

A subject's manifest lives at `subjects/{id}/subject.json` on B2 and is the
single source of truth for its status and progress — there is no database and
no in-memory job store. Every key under a subject is deterministic from the
subject id, so the frontend never supplies a prefix (sanitize-don't-trust).
"""

from datetime import UTC, datetime

from app.repo.b2_client import (
    get_bytes,
    list_keys,
    object_exists,
    put_bytes,
)
from app.types.subject import Subject

SUBJECTS_PREFIX = "subjects/"


# --- Key generators (deterministic from subject context) ---

def subject_prefix(subject_id: str) -> str:
    return f"{SUBJECTS_PREFIX}{subject_id}/"


def manifest_key(subject_id: str) -> str:
    return f"{subject_prefix(subject_id)}subject.json"


def selfie_key(subject_id: str, image_id: str, ext: str) -> str:
    ext = ext.lstrip(".").lower() or "jpg"
    return f"{subject_prefix(subject_id)}selfies/{image_id}.{ext}"


def caption_key(subject_id: str, image_id: str) -> str:
    return f"{subject_prefix(subject_id)}captions/{image_id}.txt"


def lora_key(subject_id: str) -> str:
    return f"{subject_prefix(subject_id)}model/{subject_id}.safetensors"


def headshot_key(subject_id: str, style_slug: str, index: int) -> str:
    return f"{subject_prefix(subject_id)}headshots/{style_slug}/{index:02d}.png"


# --- Manifest persistence ---

def save_manifest(subject: Subject) -> None:
    subject.updated_at = datetime.now(UTC)
    body = subject.model_dump_json(indent=2).encode("utf-8")
    put_bytes(manifest_key(subject.id), body, "application/json")


def load_manifest(subject_id: str) -> Subject | None:
    raw = get_bytes(manifest_key(subject_id))
    if raw is None:
        return None
    return Subject.model_validate_json(raw)


def manifest_exists(subject_id: str) -> bool:
    return object_exists(manifest_key(subject_id))


def list_subject_ids() -> list[str]:
    """Discover every subject id by scanning for manifest objects."""
    ids: list[str] = []
    for key in list_keys(SUBJECTS_PREFIX):
        # subjects/{id}/subject.json
        parts = key.split("/")
        if len(parts) == 3 and parts[2] == "subject.json":
            ids.append(parts[1])
    return ids


def load_all_manifests() -> list[Subject]:
    out: list[Subject] = []
    for sid in list_subject_ids():
        m = load_manifest(sid)
        if m is not None:
            out.append(m)
    return out


def read_caption(subject_id: str, image_id: str) -> str | None:
    raw = get_bytes(caption_key(subject_id, image_id))
    return raw.decode("utf-8") if raw is not None else None

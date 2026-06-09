"""Subject lifecycle: create, list, get, purge.

The manifest at subjects/{id}/subject.json is the system of record. Subject
ids are server-assigned UUIDs and all keys are derived from them, so no
user-supplied prefix ever reaches B2.
"""

import logging
import re
import uuid
from datetime import UTC, datetime

from app.config import settings
from app.repo import delete_prefix, get_presigned_url
from app.repo.subjects_store import (
    headshot_key,
    load_all_manifests,
    load_manifest,
    save_manifest,
    subject_prefix,
)
from app.service.styles import get_style_pack
from app.types.headshot import HeadshotItem, StyleSection
from app.types.subject import (
    Subject,
    SubjectStatus,
    SubjectSummary,
)

logger = logging.getLogger(__name__)

_ID_RE = re.compile(r"^[a-f0-9]{32}$")


class SubjectError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def validate_subject_id(subject_id: str) -> None:
    if not _ID_RE.match(subject_id):
        raise SubjectError("Invalid subject id", status_code=400)


def _trigger_token() -> str:
    # A rare token the LoRA binds the likeness to (kept stable per subject).
    return "sks person"


def create_subject(name: str) -> Subject:
    name = name.strip()
    if not name:
        raise SubjectError("Subject name is required")
    now = datetime.now(UTC)
    subject = Subject(
        id=uuid.uuid4().hex,
        name=name[:80],
        status=SubjectStatus.CREATED,
        created_at=now,
        updated_at=now,
        trigger_token=_trigger_token(),
        trainer_provider=settings.trainer_provider,
        generator_provider=settings.generator_provider,
    )
    save_manifest(subject)
    logger.info("Subject created: id=%s name=%s", subject.id, subject.name)
    return subject


def get_subject(subject_id: str) -> Subject:
    validate_subject_id(subject_id)
    subject = load_manifest(subject_id)
    if subject is None:
        raise SubjectError("Subject not found", status_code=404)
    return subject


def list_subjects() -> list[SubjectSummary]:
    summaries: list[SubjectSummary] = []
    for m in load_all_manifests():
        cover = m.headshots[0].key if m.headshots else None
        summaries.append(
            SubjectSummary(
                id=m.id,
                name=m.name,
                status=m.status,
                created_at=m.created_at,
                updated_at=m.updated_at,
                selfie_count=len(m.selfies),
                headshot_count=len(m.headshots),
                cover_key=cover,
            )
        )
    summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries


def purge_subject(subject_id: str) -> int:
    """Privacy lifecycle: batch-delete EVERY object under subjects/{id}/.

    Removes selfies, captions, the trained LoRA, all headshots, and the
    manifest in one sweep. Returns the number of objects deleted.
    """
    validate_subject_id(subject_id)
    prefix = subject_prefix(subject_id)
    deleted = delete_prefix(prefix)
    logger.info("Subject purged: id=%s objects_deleted=%d", subject_id, deleted)
    return deleted


def get_subject_gallery(subject_id: str) -> list[StyleSection]:
    """Group a subject's headshots by style pack, with presigned preview URLs."""
    subject = get_subject(subject_id)
    by_style: dict[str, list[HeadshotItem]] = {}
    for ref in subject.headshots:
        pack = get_style_pack(ref.style_slug)
        if pack is None:
            continue
        url = get_presigned_url(ref.key, expires_in=600)
        by_style.setdefault(ref.style_slug, []).append(
            HeadshotItem(
                key=ref.key,
                style_slug=ref.style_slug,
                index=ref.index,
                url=url,
            )
        )
    sections: list[StyleSection] = []
    for slug, items in by_style.items():
        pack = get_style_pack(slug)
        if pack is None:
            continue
        items.sort(key=lambda h: h.index)
        sections.append(StyleSection(style=pack, headshots=items))
    return sections


def headshot_preview_url(subject_id: str, style_slug: str, index: int) -> str:
    validate_subject_id(subject_id)
    return get_presigned_url(headshot_key(subject_id, style_slug, index))

"""Selfie ingestion + captioning.

Selfies are written under the subject's own prefix (separate from the generic
/upload `uploads/` prefix) so the privacy purge can sweep them. Captioning is
peripheral — it runs Claude vision when a key is set, otherwise a templated
caption — and conditions the LoRA training that follows.
"""

import logging
import uuid

from app.repo import get_bytes, put_bytes
from app.repo.captioner import caption_selfie
from app.repo.subjects_store import caption_key, save_manifest, selfie_key
from app.service.subjects import SubjectError, get_subject
from app.types.subject import SelfieRef, Subject, SubjectStatus

logger = logging.getLogger(__name__)

_ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def add_selfie(
    subject_id: str,
    file_data: bytes,
    filename: str,
    content_type: str,
) -> Subject:
    """Attach one selfie to a subject. Raises SubjectError on validation fail."""
    subject = get_subject(subject_id)
    if subject.status in (SubjectStatus.TRAINING, SubjectStatus.GENERATING):
        raise SubjectError("Cannot add selfies while a job is running", 409)
    ext = _ALLOWED_IMAGE_TYPES.get(content_type)
    if ext is None:
        raise SubjectError(
            "Selfies must be JPEG, PNG, or WebP", status_code=415
        )
    if len(file_data) == 0:
        raise SubjectError("Empty file")

    image_id = uuid.uuid4().hex[:12]
    key = selfie_key(subject_id, image_id, ext)
    put_bytes(key, file_data, content_type)
    subject.selfies.append(
        SelfieRef(image_id=image_id, key=key, filename=filename or f"{image_id}.{ext}")
    )
    save_manifest(subject)
    logger.info("Selfie added: subject=%s image=%s", subject_id, image_id)
    return subject


def caption_subject(subject_id: str) -> Subject:
    """Caption every uncaptioned selfie, then mark the subject ready to train.

    Runs inline (a handful of small calls). Stores one caption per selfie at
    subjects/{id}/captions/{image_id}.txt and records it in the manifest.
    """
    subject = get_subject(subject_id)
    if not subject.selfies:
        raise SubjectError("Add selfies before captioning")
    subject.status = SubjectStatus.CAPTIONING
    save_manifest(subject)
    try:
        for ref in subject.selfies:
            if ref.caption:
                continue
            data = get_bytes(ref.key)
            if data is None:
                continue
            ext = ref.key.rsplit(".", 1)[-1]
            caption = caption_selfie(data, ext, subject.trigger_token)
            put_bytes(caption_key(subject_id, ref.image_id), caption.encode("utf-8"), "text/plain")
            ref.caption = caption
        subject.status = SubjectStatus.READY_TO_TRAIN
        save_manifest(subject)
    except Exception as e:
        subject.status = SubjectStatus.FAILED
        subject.error = f"Captioning failed: {e}"
        save_manifest(subject)
        raise
    logger.info("Subject captioned: id=%s selfies=%d", subject_id, len(subject.selfies))
    return subject

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile

from app.config import settings
from app.service.captioning import add_selfie, caption_subject
from app.service.subjects import (
    SubjectError,
    create_subject,
    get_subject,
    list_subjects,
    purge_subject,
)
from app.service.training import run_training, start_training
from app.types.subject import (
    CreateSubjectRequest,
    Subject,
    SubjectSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _handle(e: SubjectError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/subjects", response_model=list[SubjectSummary])
async def list_subjects_endpoint():
    return list_subjects()


@router.post("/subjects", response_model=Subject)
async def create_subject_endpoint(body: CreateSubjectRequest):
    try:
        return create_subject(body.name)
    except SubjectError as e:
        raise _handle(e) from None


@router.get("/subjects/{subject_id}", response_model=Subject)
async def get_subject_endpoint(subject_id: str):
    try:
        return get_subject(subject_id)
    except SubjectError as e:
        raise _handle(e) from None


@router.get("/subjects/{subject_id}/progress")
async def subject_progress_endpoint(subject_id: str):
    """Lightweight status poll — drives the Studio/Gallery progress UI."""
    try:
        s = get_subject(subject_id)
    except SubjectError as e:
        raise _handle(e) from None
    return {
        "status": s.status,
        "train_steps_done": s.train_steps_done,
        "train_steps_total": s.train_steps_total,
        "headshots_done": s.headshots_done,
        "headshots_total": s.headshots_total,
        "error": s.error,
    }


@router.post("/subjects/{subject_id}/selfies", response_model=Subject)
async def add_selfie_endpoint(subject_id: str, request: Request, file: UploadFile):
    content_type = file.content_type or "application/octet-stream"
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")
        chunks.append(chunk)
    try:
        return add_selfie(
            subject_id,
            file_data=b"".join(chunks),
            filename=file.filename or "",
            content_type=content_type,
        )
    except SubjectError as e:
        raise _handle(e) from None


@router.post("/subjects/{subject_id}/caption", response_model=Subject)
async def caption_endpoint(subject_id: str):
    try:
        return caption_subject(subject_id)
    except SubjectError as e:
        raise _handle(e) from None


@router.post("/subjects/{subject_id}/train", response_model=Subject)
async def train_endpoint(subject_id: str, background: BackgroundTasks):
    try:
        subject = start_training(subject_id)
    except SubjectError as e:
        raise _handle(e) from None
    background.add_task(run_training, subject_id)
    return subject


@router.delete("/subjects/{subject_id}")
async def purge_endpoint(subject_id: str):
    """Face-data privacy purge — batch-delete the whole subjects/{id}/ prefix."""
    try:
        deleted = purge_subject(subject_id)
    except SubjectError as e:
        raise _handle(e) from None
    except RuntimeError:
        raise HTTPException(status_code=500, detail="Failed to purge subject") from None
    return {"purged": True, "subject_id": subject_id, "objects_deleted": deleted}

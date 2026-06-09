import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.service.generation import run_generation, start_generation
from app.service.stats import get_studio_stats
from app.service.styles import list_style_packs
from app.service.subjects import (
    SubjectError,
    get_subject_gallery,
)
from app.types.headshot import StyleSection
from app.types.stats import StudioStats
from app.types.style import StylePack
from app.types.subject import GenerateRequest, Subject

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/styles", response_model=list[StylePack])
async def styles_endpoint():
    return list_style_packs()


@router.get("/stats/studio", response_model=StudioStats)
async def studio_stats_endpoint():
    return get_studio_stats()


@router.get("/subjects/{subject_id}/gallery", response_model=list[StyleSection])
async def gallery_endpoint(subject_id: str):
    try:
        return get_subject_gallery(subject_id)
    except SubjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None


@router.post("/subjects/{subject_id}/generate", response_model=Subject)
async def generate_endpoint(
    subject_id: str, body: GenerateRequest, background: BackgroundTasks
):
    try:
        subject = start_generation(subject_id, body.style_slugs)
    except SubjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None
    background.add_task(run_generation, subject_id)
    return subject

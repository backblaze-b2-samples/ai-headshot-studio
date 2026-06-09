"""Generation job orchestration.

Runs as a FastAPI BackgroundTask. Renders `headshots_per_style` real images
for each selected style pack from the subject's trained LoRA, writing each PNG
to B2 and appending a HeadshotRef to the manifest. Progress lives in the
manifest (`headshots_done` / `headshots_total`) and the frontend polls it.
"""

import logging

from app.config import settings
from app.repo.generator import GenerateImageRequest, get_generator
from app.repo.subjects_store import load_manifest, save_manifest
from app.service.styles import build_prompt, get_style_pack, valid_slugs
from app.service.subjects import SubjectError, get_subject
from app.types.subject import HeadshotRef, Subject, SubjectStatus

logger = logging.getLogger(__name__)


def start_generation(subject_id: str, style_slugs: list[str]) -> Subject:
    """Validate and flip into GENERATING. Caller schedules run_generation."""
    subject = get_subject(subject_id)
    if subject.status not in (
        SubjectStatus.TRAINED,
        SubjectStatus.COMPLETE,
    ):
        raise SubjectError("Train the subject before generating", 409)
    if not subject.lora_key:
        raise SubjectError("Subject has no trained model", 409)
    slugs = valid_slugs(style_slugs)
    if not slugs:
        raise SubjectError("Select at least one valid style pack")

    subject.styles_requested = slugs
    subject.status = SubjectStatus.GENERATING
    subject.headshots_done = 0
    subject.headshots_total = len(slugs) * settings.headshots_per_style
    subject.error = None
    save_manifest(subject)
    return subject


def run_generation(subject_id: str) -> None:
    """Background entrypoint — renders REAL headshots across the style packs."""
    subject = load_manifest(subject_id)
    if subject is None:
        logger.error("run_generation: subject %s vanished", subject_id)
        return
    if not subject.lora_key:
        return
    try:
        generator = get_generator()
        per_style = settings.headshots_per_style
        done = 0

        def on_image(img) -> None:
            nonlocal done
            done += 1
            subject.headshots.append(
                HeadshotRef(style_slug=img.style_slug, key=img.key, index=img.index)
            )
            subject.headshots_done = done
            save_manifest(subject)

        for slug in subject.styles_requested:
            pack = get_style_pack(slug)
            if pack is None:
                continue
            # Continue numbering after any headshots already rendered for this style.
            existing = [h.index for h in subject.headshots if h.style_slug == slug]
            start_index = (max(existing) + 1) if existing else 0
            generator.generate(
                GenerateImageRequest(
                    subject_id=subject.id,
                    lora_key=subject.lora_key,
                    trigger_token=subject.trigger_token,
                    style_slug=slug,
                    prompt=build_prompt(slug, subject.trigger_token),
                    negative_prompt=pack.negative_prompt,
                    count=per_style,
                    steps=settings.generate_steps,
                    guidance=settings.generate_guidance,
                    start_index=start_index,
                ),
                on_image,
            )

        subject.status = SubjectStatus.COMPLETE
        subject.error = None
        save_manifest(subject)
        logger.info("Generation complete: subject=%s headshots=%d", subject_id, done)
    except Exception as e:
        logger.error("Generation failed: subject=%s err=%s", subject_id, e, exc_info=True)
        subject.status = SubjectStatus.FAILED
        subject.error = f"Generation failed: {e}"
        save_manifest(subject)

"""Headshot dashboard aggregations.

Computes domain metrics (subjects, headshots generated, models trained, B2
storage used) and a storage breakdown by artifact type, scoped to the
`subjects/` prefix. Categorizes each object by its key segment.
"""

from app.repo import list_files
from app.repo.subjects_store import SUBJECTS_PREFIX, load_all_manifests
from app.types.formatting import humanize_bytes
from app.types.stats import StorageSlice, StudioStats


def _categorize(key: str) -> str:
    # subjects/{id}/<bucket>/...
    parts = key.split("/")
    if len(parts) < 3:
        return "other"
    segment = parts[2]
    if segment == "selfies":
        return "selfies"
    if segment == "captions":
        return "captions"
    if segment == "model":
        return "models"
    if segment == "headshots":
        return "headshots"
    return "other"


def get_studio_stats() -> StudioStats:
    files = list_files(prefix=SUBJECTS_PREFIX, max_keys=1000)
    manifests = load_all_manifests()

    buckets: dict[str, dict] = {}
    total_bytes = 0
    headshots_generated = 0
    for f in files:
        total_bytes += f.size_bytes
        cat = _categorize(f.key)
        if cat == "headshots":
            headshots_generated += 1
        slot = buckets.setdefault(cat, {"size": 0, "count": 0})
        slot["size"] += f.size_bytes
        slot["count"] += 1

    models_trained = sum(1 for m in manifests if m.lora_key)

    order = ["selfies", "captions", "models", "headshots", "other"]
    breakdown = [
        StorageSlice(
            category=cat,
            size_bytes=buckets[cat]["size"],
            size_human=humanize_bytes(buckets[cat]["size"]),
            object_count=buckets[cat]["count"],
        )
        for cat in order
        if cat in buckets
    ]

    return StudioStats(
        subjects=len(manifests),
        headshots_generated=headshots_generated,
        models_trained=models_trained,
        storage_bytes=total_bytes,
        storage_human=humanize_bytes(total_bytes),
        breakdown=breakdown,
    )

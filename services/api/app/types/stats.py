from pydantic import BaseModel


class DailyUploadCount(BaseModel):
    date: str
    uploads: int


class UploadStats(BaseModel):
    """Aggregate bucket stats — backs the kept full-bucket /files view."""

    total_files: int
    total_size_bytes: int
    total_size_human: str
    uploads_today: int
    total_downloads: int


class StorageSlice(BaseModel):
    """One artifact category in the dashboard storage breakdown."""

    category: str  # selfies | captions | models | headshots | other
    size_bytes: int
    size_human: str
    object_count: int


class StudioStats(BaseModel):
    """Headshot-domain dashboard metrics, aggregated from the subjects/ prefix."""

    subjects: int
    headshots_generated: int
    models_trained: int
    storage_bytes: int
    storage_human: str
    breakdown: list[StorageSlice]

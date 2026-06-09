"""Tests for subject key generation, id validation, and the captioner fallback.

These are hermetic — no B2 calls. They lock the deterministic key layout
(subjects/{id}/...) and the privacy-relevant invariant that user input never
forms a prefix.
"""

import pytest

from app.repo import subjects_store as store
from app.repo.captioner import caption_selfie
from app.service.subjects import SubjectError, validate_subject_id

SID = "0123456789abcdef0123456789abcdef"


def test_key_layout_is_deterministic_and_scoped():
    assert store.subject_prefix(SID) == f"subjects/{SID}/"
    assert store.manifest_key(SID) == f"subjects/{SID}/subject.json"
    assert store.selfie_key(SID, "img1", "png") == f"subjects/{SID}/selfies/img1.png"
    assert store.caption_key(SID, "img1") == f"subjects/{SID}/captions/img1.txt"
    assert store.lora_key(SID) == f"subjects/{SID}/model/{SID}.safetensors"
    assert (
        store.headshot_key(SID, "corporate", 3)
        == f"subjects/{SID}/headshots/corporate/03.png"
    )


def test_selfie_key_normalizes_extension():
    assert store.selfie_key(SID, "x", ".JPG") == f"subjects/{SID}/selfies/x.jpg"
    assert store.selfie_key(SID, "x", "") == f"subjects/{SID}/selfies/x.jpg"


def test_validate_subject_id_rejects_bad_ids():
    validate_subject_id(SID)  # ok
    for bad in ("", "../etc", "short", "g" * 32, SID + "z"):
        with pytest.raises(SubjectError):
            validate_subject_id(bad)


def test_captioner_falls_back_without_key(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "anthropic_api_key", "")
    caption = caption_selfie(b"not-a-real-image", "jpg", "sks person")
    assert "sks person" in caption

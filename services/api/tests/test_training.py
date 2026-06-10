"""Tests for the training step-budget resolution."""

import pytest

from app.config import settings
from app.service.training import effective_train_steps


@pytest.fixture
def auto_budget(monkeypatch):
    """Auto mode: scale by image count, clamp to [600, 1200], 100/image."""
    monkeypatch.setattr(settings, "train_steps", 0)
    monkeypatch.setattr(settings, "train_steps_per_image", 100)
    monkeypatch.setattr(settings, "train_steps_min", 600)
    monkeypatch.setattr(settings, "train_steps_max", 1200)


def test_scales_with_image_count(auto_budget):
    assert effective_train_steps(8) == 800


def test_clamps_small_set_up_to_min(auto_budget):
    # 2 selfies * 100 = 200, below the 600 floor.
    assert effective_train_steps(2) == 600


def test_clamps_large_set_down_to_max(auto_budget):
    # 50 selfies * 100 = 5000, above the 1200 ceiling.
    assert effective_train_steps(50) == 1200


def test_zero_images_does_not_divide_by_zero(auto_budget):
    # Degenerate input still resolves to the floor, never a crash.
    assert effective_train_steps(0) == 600


def test_explicit_override_wins(monkeypatch):
    # A pinned train_steps (e.g. TRAIN_STEPS=40 for a smoke test) bypasses
    # the per-image scaling entirely.
    monkeypatch.setattr(settings, "train_steps", 40)
    assert effective_train_steps(20) == 40

"""Tests for the style-pack registry and prompt building."""

from app.service.styles import (
    build_prompt,
    get_style_pack,
    list_style_packs,
    valid_slugs,
)


def test_built_in_packs_present():
    slugs = {p.slug for p in list_style_packs()}
    assert {"corporate", "linkedin", "creative", "outdoor", "editorial-bw"} <= slugs


def test_every_template_has_subject_placeholder():
    for pack in list_style_packs():
        assert "{subject}" in pack.prompt_template


def test_build_prompt_substitutes_trigger_token():
    prompt = build_prompt("corporate", "sks person")
    assert "sks person" in prompt
    assert "{subject}" not in prompt


def test_get_style_pack_unknown_returns_none():
    assert get_style_pack("does-not-exist") is None


def test_valid_slugs_filters_unknowns_and_dupes():
    assert valid_slugs(["corporate", "bogus", "corporate", "linkedin"]) == [
        "corporate",
        "linkedin",
    ]

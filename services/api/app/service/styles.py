"""Style-pack registry.

Curated headshot looks, data-driven so new packs are a one-line addition.
Each `prompt_template` carries a `{subject}` placeholder filled with the
subject's trigger token at generation time. Adding a pack here is all it takes
for it to appear in the Studio picker and the Gallery sections.
"""

from app.types.style import StylePack

_STYLE_PACKS: list[StylePack] = [
    StylePack(
        slug="corporate",
        label="Corporate",
        description="Studio-lit business portrait against a clean neutral backdrop.",
        prompt_template=(
            "professional corporate headshot of {subject}, business attire, "
            "soft studio lighting, neutral gray background, sharp focus, "
            "confident expression, 85mm portrait lens, high detail"
        ),
    ),
    StylePack(
        slug="linkedin",
        label="LinkedIn",
        description="Approachable professional profile photo, natural daylight.",
        prompt_template=(
            "friendly linkedin profile headshot of {subject}, smart casual, "
            "natural window light, soft bokeh office background, warm tone, "
            "approachable smile, crisp focus"
        ),
    ),
    StylePack(
        slug="creative",
        label="Creative",
        description="Colorful, characterful portrait with dramatic lighting.",
        prompt_template=(
            "creative editorial portrait of {subject}, colorful rim lighting, "
            "moody gradient background, cinematic mood, shallow depth of field, "
            "expressive, fashion photography"
        ),
    ),
    StylePack(
        slug="outdoor",
        label="Outdoor",
        description="Golden-hour environmental portrait outdoors.",
        prompt_template=(
            "outdoor environmental portrait of {subject}, golden hour sunlight, "
            "blurred natural greenery background, warm rim light, candid, "
            "lifestyle photography, sharp eyes"
        ),
    ),
    StylePack(
        slug="editorial-bw",
        label="Editorial B&W",
        description="High-contrast black-and-white editorial headshot.",
        prompt_template=(
            "dramatic black and white editorial headshot of {subject}, "
            "high contrast monochrome, single key light, deep shadows, "
            "fine grain, magazine cover style, intense gaze"
        ),
    ),
]

_BY_SLUG = {pack.slug: pack for pack in _STYLE_PACKS}


def list_style_packs() -> list[StylePack]:
    return list(_STYLE_PACKS)


def get_style_pack(slug: str) -> StylePack | None:
    return _BY_SLUG.get(slug)


def valid_slugs(slugs: list[str]) -> list[str]:
    """Filter to known slugs, preserving order and dropping unknowns/dupes."""
    seen: set[str] = set()
    out: list[str] = []
    for s in slugs:
        if s in _BY_SLUG and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def build_prompt(slug: str, trigger_token: str) -> str:
    pack = _BY_SLUG[slug]
    return pack.prompt_template.format(subject=trigger_token)

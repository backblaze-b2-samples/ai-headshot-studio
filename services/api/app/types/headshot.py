from pydantic import BaseModel

from app.types.style import StylePack


class HeadshotItem(BaseModel):
    """A single rendered headshot with a short-lived presigned preview URL."""

    key: str
    style_slug: str
    index: int
    url: str


class StyleSection(BaseModel):
    """A style pack plus the headshots rendered for the subject in that style."""

    style: StylePack
    headshots: list[HeadshotItem]

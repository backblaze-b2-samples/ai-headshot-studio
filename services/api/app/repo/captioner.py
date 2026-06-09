"""Optional selfie auto-captioning.

Peripheral feature: when ANTHROPIC_API_KEY is set, each selfie gets a short
caption from Claude vision (model `claude-haiku-4-5`, the cheapest vision tier
— ~10-20 small calls per subject, well under the $1 budget). When unset, a
templated caption is used instead, so the default path needs no key. The
`anthropic` SDK is lazy-imported here only.

A good caption conditions training better, but it is NOT the core capability —
training+generation work fine on the templated fallback.
"""

import base64
import logging

from app.config import settings

logger = logging.getLogger(__name__)

_PROMPT = (
    "Write a single concise training caption for this selfie of a person. "
    "Describe pose, framing, expression, lighting and background in under 20 "
    "words. Do not name the person. Reply with only the caption."
)


def _media_type(ext: str) -> str:
    ext = ext.lstrip(".").lower()
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }.get(ext, "image/jpeg")


def caption_selfie(image_bytes: bytes, ext: str, trigger_token: str) -> str:
    """Return a caption for one selfie. Falls back to a template on any error
    or when no API key is configured."""
    fallback = f"a photo of {trigger_token}, a person, headshot"
    if not settings.anthropic_api_key:
        return fallback
    try:
        import anthropic  # lazy

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        b64 = base64.standard_b64encode(image_bytes).decode("ascii")
        message = client.messages.create(
            model=settings.caption_model,
            max_tokens=80,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": _media_type(ext),
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": _PROMPT},
                    ],
                }
            ],
        )
        text = "".join(
            block.text for block in message.content if block.type == "text"
        ).strip()
        if not text:
            return fallback
        # Bind the caption to the subject's trigger token for the LoRA.
        return f"{trigger_token}, {text}"
    except Exception:
        logger.warning("Claude captioning failed; using templated caption", exc_info=True)
        return fallback

from pydantic import BaseModel


class StylePack(BaseModel):
    """A curated headshot style: a slug, label, and the prompt scaffolding
    used to render the subject in that look. `prompt_template` must contain
    a `{subject}` placeholder that gets filled with the subject's trigger
    token at generation time.
    """

    slug: str
    label: str
    description: str
    prompt_template: str
    negative_prompt: str = (
        "blurry, low quality, lowres, deformed, disfigured, bad anatomy, "
        "extra limbs, extra fingers, mutated hands, cropped, worst quality, "
        "jpeg artifacts, plastic skin, oversaturated, closed eyes, watermark, "
        "text, cartoon, 3d render"
    )

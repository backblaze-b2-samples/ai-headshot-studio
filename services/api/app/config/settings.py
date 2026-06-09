from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Backblaze B2 (S3-compatible) ---
    b2_endpoint: str = "https://s3.us-west-004.backblazeb2.com"
    b2_region: str = "us-west-004"
    b2_application_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = ""
    b2_public_url: str = ""

    api_port: int = 8000
    # Explicit allowlist by default — covers Next on :3000 and the
    # fallback :3001 it picks if 3000 is busy. Production deploys should
    # override with the exact frontend origin.
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    # Optional dev-only escape hatch: a regex that matches additional
    # allowed origins. Empty by default — set this to e.g.
    # `^http://localhost:\d+$` to accept any localhost port without
    # listing each one. NEVER ship this to production.
    api_cors_origin_regex: str = ""

    # Upload limits
    max_file_size: int = 100 * 1024 * 1024  # 100MB

    # Small durable counters (downloads, etc). Point at a persistent
    # volume in production if you care about surviving restarts.
    download_count_file: str = "data/download_count.json"

    # --- Headshot studio: training & generation engines ---
    # Engine selection. "local" (default) does REAL SD-1.5 LoRA fine-tuning
    # and generation via diffusers+peft at $0 / no keys. "replicate" is a
    # real, opt-in hosted FLUX path that needs REPLICATE_API_TOKEN and costs
    # money — never the default.
    trainer_provider: str = "local"
    generator_provider: str = "local"

    # Base diffusion model for the local engine. The default is SD-1.5; the
    # verification harness overrides this with a tiny test pipeline.
    base_model: str = "runwayml/stable-diffusion-v1-5"
    # Replicate hosted-model slugs (FLUX LoRA train + generate).
    replicate_train_model: str = (
        "ostris/flux-dev-lora-trainer:"
        "e440909d3512c31646ee2e0c7d6f6f4923224863a6a10c494606e79fb5844497"
    )
    replicate_generate_model: str = "black-forest-labs/flux-dev-lora"

    # Training hyperparameters (kept small so the default local run is feasible
    # on CPU/MPS; crank up for quality on a GPU).
    train_steps: int = 600
    train_resolution: int = 512
    train_lora_rank: int = 8
    train_learning_rate: float = 1e-4
    # How many headshots to render per selected style pack. Default 6 -> ~30
    # across the five built-in packs; raise toward "hundreds".
    headshots_per_style: int = 6
    generate_steps: int = 25
    generate_guidance: float = 7.5
    # Minimum / maximum selfies accepted for a subject.
    min_selfies: int = 4
    max_selfies: int = 30

    # --- Optional external APIs (never required; keys live outside B2 vars) ---
    # Anthropic Claude vision for selfie auto-captioning. Falls back to a
    # templated caption when unset.
    anthropic_api_key: str = ""
    caption_model: str = "claude-haiku-4-5"
    # Replicate API token for the hosted FLUX path.
    replicate_api_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]


settings = Settings()

"""
config.py - Application configuration for AgroGuard-AI (Banana Edition).
Loads settings from .env file using pydantic-settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All application settings. Override via environment variables or .env file."""

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:0308@localhost:5432/agroguard_banana"
    )

    # ── ML Model ───────────────────────────────────────────────────────
    MODEL_PATH: str = "saved_models/agroguard_banana_resnet50.pth"

    # ── Server ─────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ── CORS ───────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()

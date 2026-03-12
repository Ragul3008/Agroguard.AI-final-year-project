"""
config.py - Production configuration for AgroGuard-AI v1.2.0
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Production application settings."""

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:0308@localhost:5432/agroguard_banana"

    # ── ML Model ───────────────────────────────────────────────────────
    MODEL_PATH: str                   = "saved_models/agroguard_banana_resnet50.pth"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.75
    MODEL_NOT_BANANA_THRESHOLD: float = 0.40

    # ── Gemini LLM ─────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ── Google Maps ────────────────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""

    # ── JWT Authentication ─────────────────────────────────────────────
    SECRET_KEY: str = "agroguard-secret-key-change-this-in-production"

    # ── Whisper ────────────────────────────────────────────────────────
    WHISPER_MODEL_SIZE: str = "medium"

    # ── Server ─────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool   = False

    # ── CORS ───────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()
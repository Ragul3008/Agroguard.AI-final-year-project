"""
config.py - Production configuration for AgroGuard-AI v2.0.0
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Production application settings."""

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:0308@localhost:5432/agroguard_banana"

    # ── ML Model ───────────────────────────────────────────────────────
    MODEL_PATH: str                   = "saved_models/agroguard_banana_convnext_v3.pth"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.75
    MODEL_NOT_BANANA_THRESHOLD: float = 0.40

    # ── Gemini LLM ─────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ── Location APIs ──────────────────────────────────────────────────
    GEOAPIFY_API_KEY: str    = ""   # Primary   — Geoapify Places API (3000/day free)
    GOOGLE_MAPS_API_KEY: str = ""   # Secondary — Google Maps (kept as backup)

    # ── JWT Authentication ─────────────────────────────────────────────
    SECRET_KEY: str = "agroguard-secret-key-change-this-in-production"
    REFRESH_SECRET_KEY: str = "agroguard-refresh-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Google OAuth ───────────────────────────────────────────────────
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""

    # ── Email (for password reset OTP) ─────────────────────────────────
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM_ADDRESS: str = "noreply@agroguard.ai"

    # ── Whisper ────────────────────────────────────────────────────────
    WHISPER_MODEL_SIZE: str = "medium"

    # ── Server ─────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PORT: int = 8000  # Render injects PORT env var
    DEBUG: bool   = False

    # ── CORS ───────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins. Supports wildcards like https://*.vercel.app
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://agroguard.vercel.app,https://*.vercel.app"

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        extra             = "ignore"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list, expanding wildcard patterns."""
        origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        # For wildcard subdomains like https://*.vercel.app, we'll handle in middleware
        return origins


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()
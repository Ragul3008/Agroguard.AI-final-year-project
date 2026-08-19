"""
main.py - AgroGuard-AI Production FastAPI Application v1.2.0

All endpoints are versioned under /api/v1/

Endpoints:
    /api/v1/auth/register
    /api/v1/auth/login
    /api/v1/auth/me
    /api/v1/predict
    /api/v1/predictions
    /api/v1/predictions/stats
    /api/v1/speech/transcribe
    /api/v1/speech/process
    /health  ← unversioned (monitoring)

Team: Kabilan R K | Ragul J | Sanjai J | Karthikeyan S
Guide: Dr. G. Arulselvi — Annamalai University B.E CSE (AI & ML)
"""

import asyncio
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.database.db import create_tables
from app.models.model_loader import ModelLoader
from app.api.health import router as health_router
from app.api.routes import router as predict_router
from app.api.speech import router as speech_router
from app.api.auth import router as auth_router
from app.utils.rate_limiter import limiter
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# API version prefix
# ---------------------------------------------------------------------------
API_V1 = "/api/v1"


def _expand_wildcard_origins(origins: list[str]) -> list[str]:
    """Expand wildcard patterns like https://*.vercel.app to regex patterns for CORS."""
    expanded = []
    for origin in origins:
        if "*" in origin:
            # Convert wildcard to regex pattern for CORS allow_origin_regex
            pattern = origin.replace(".", r"\.").replace("*", ".*")
            expanded.append(pattern)
        else:
            expanded.append(origin)
    return expanded


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║  AgroGuard-AI STARTING  ║")
    logger.info("╚══════════════════════════════════════════════╝")

    try:
        await create_tables()
        logger.info("✓ Database tables ready.")
    except Exception as exc:
        logger.error("✗ Database failed: %s", exc)
        logger.warning("  Continuing without DB.")

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: ModelLoader.get_instance(settings.MODEL_PATH),
        )
        logger.info("✓ Banana disease model loaded and ready.")
    except Exception as exc:
        logger.error("✗ Model loading failed: %s", exc)

    logger.info("✓ AgroGuard-AI is ready → base URL: %s", API_V1)

    yield

    logger.info("AgroGuard-AI shutting down gracefully.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgroGuard-AI — Banana Disease Detection",
        description=(
            "## AI-Powered Banana Crop Disease Detection\n\n"
            "**Annamalai University — B.E CSE (AI & ML) Final Year Project**\n\n"
            "### Base URL\n"
            "All endpoints are under `/api/v1/`\n\n"
            "### How to Use\n"
            "1. 📝 **Register** → `POST /api/v1/auth/register`\n"
            "2. 🔐 **Login** → `POST /api/v1/auth/login` → copy `access_token`\n"
            "3. 🔑 Click **Authorize** button → paste token\n"
            "4. 🍌 **Upload image** → `POST /api/v1/predict`\n\n"
            "### Features\n"
            "- 🍌 Detects 6 banana diseases + healthy classification\n"
            "- 🔐 JWT Authentication (farmer accounts)\n"
            "- 🤖 Gemini LLM-powered ICAR advisories\n"
            "- 🗺️ Google Maps nearest centre detection\n"
            "- 🎤 Multilingual speech-to-text (Whisper medium)\n"
            "- 📊 Prediction history & statistics\n"
            "- 🛡️ Rate limiting (abuse prevention)\n"
            "- 🔢 API versioning (/api/v1/)\n\n"
            "### Rate Limits\n"
            "- `/predict` → 10 requests/minute\n"
            "- `/auth/login` → 10 requests/minute\n"
            "- `/auth/register` → 5 requests/minute\n\n"
            "### Team\n"
            "Kabilan R K | Ragul J | Sanjai J | Karthikeyan S\n\n"
            "**Guide:** Dr. G. Arulselvi"
        ),
        version="1.2.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Rate limiting ──────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS ───────────────────────────────────────────────────────────
    allowed_origins = settings.allowed_origins_list
    # Separate exact origins from wildcard patterns
    exact_origins = [o for o in allowed_origins if "*" not in o]
    wildcard_patterns = [o for o in allowed_origins if "*" in o]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=exact_origins if exact_origins else ["http://localhost:5173"],
        allow_origin_regex="|".join(wildcard_patterns) if wildcard_patterns else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers (all under /api/v1/) ───────────────────────────────────
    app.include_router(health_router)                              # /health (unversioned)
    app.include_router(auth_router,    prefix=API_V1)             # /api/v1/auth/...
    app.include_router(predict_router, prefix=API_V1)             # /api/v1/predict
    app.include_router(speech_router,  prefix=API_V1)             # /api/v1/speech/...

    return app


app = create_app()
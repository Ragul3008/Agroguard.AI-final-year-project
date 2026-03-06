"""
main.py - AgroGuard-AI Production FastAPI Application v1.1.0

Team: Kabilan R K | Ragul J | Sanjai J | Karthikeyan S
Guide: Dr. G. Arulselvi — Annamalai University B.E CSE (AI & ML)

Run:
    uvicorn app.main:app --reload
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.db import create_tables
from app.models.model_loader import ModelLoader
from app.api.health import router as health_router
from app.api.routes import router as predict_router
from app.api.speech import router as speech_router
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║  AgroGuard-AI v1.1.0 (Production) STARTING  ║")
    logger.info("╚══════════════════════════════════════════════╝")

    try:
        await create_tables()
        logger.info("✓ Database tables ready.")
    except Exception as exc:
        logger.error("✗ Database failed: %s", exc)
        logger.warning("  Continuing without DB — predictions will not be persisted.")

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: ModelLoader.get_instance(settings.MODEL_PATH),
        )
        logger.info("✓ Banana disease model loaded and ready.")
    except Exception as exc:
        logger.error("✗ Model loading failed: %s", exc)
        logger.warning("  Continuing with uninitialised model.")

    logger.info("✓ AgroGuard-AI is ready to serve requests.")

    yield

    logger.info("AgroGuard-AI shutting down gracefully.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgroGuard-AI — Banana Disease Detection",
        description=(
            "## AI-Powered Banana Crop Disease Detection\n\n"
            "**Annamalai University — B.E CSE (AI & ML) Final Year Project**\n\n"
            "### Features\n"
            "- 🍌 Detects 6 banana diseases + healthy classification\n"
            "- 🎯 Confidence threshold filtering\n"
            "- 🚫 Non-banana image rejection\n"
            "- 📊 Full probability distribution for all 7 classes\n"
            "- 📋 ICAR-aligned treatment advisories\n"
            "- 📍 Nearest banana farming support centre\n"
            "- 🎤 Multilingual speech-to-text (Whisper medium)\n"
            "- 📈 Prediction history & statistics dashboard\n\n"
            "### Team\n"
            "Kabilan R K | Ragul J | Sanjai J | Karthikeyan S\n\n"
            "**Guide:** Dr. G. Arulselvi"
        ),
        version="1.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(predict_router)
    app.include_router(speech_router)

    return app


app = create_app()
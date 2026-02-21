"""
main.py - AgroGuard-AI FastAPI application entry point (Banana Edition).

Startup sequence:
    1. Initialise PostgreSQL tables via SQLAlchemy.
    2. Pre-load the ResNet-50 banana disease model into memory (singleton).
    3. Register CORS middleware and API routers.
    4. Serve requests via Uvicorn.

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
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan context — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles application startup and shutdown logic.

    Startup:
        1. Create / verify PostgreSQL tables.
        2. Warm up the ResNet-50 banana model.

    Shutdown:
        Resources are cleaned up automatically by SQLAlchemy's NullPool.
    """
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║   AgroGuard-AI (Banana Edition) STARTING ║")
    logger.info("╚══════════════════════════════════════════╝")

    # ── 1. Database initialisation ────────────────────────────────────────
    try:
        await create_tables()
        logger.info("✓ Database tables ready.")
    except Exception as exc:
        logger.error("✗ Database initialisation failed: %s", exc)
        logger.warning("  Continuing without DB — predictions will not be persisted.")

    # ── 2. Model warm-up ──────────────────────────────────────────────────
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: ModelLoader.get_instance(settings.MODEL_PATH),
        )
        logger.info("✓ Banana disease model loaded and ready.")
    except Exception as exc:
        logger.error("✗ Model loading failed: %s", exc)
        logger.warning("  Continuing with uninitialised model — predictions will fail.")

    logger.info("✓ AgroGuard-AI is ready to serve requests.")

    yield  # ← application runs here

    logger.info("AgroGuard-AI shutting down gracefully.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""

    app = FastAPI(
        title="AgroGuard-AI — Banana Disease Detection",
        description=(
            "AI-powered banana crop disease detection API.\n\n"
            "Detects: Panama Disease, Black Sigatoka, Yellow Sigatoka, "
            "Pseudostem Weevil, Bunchy Top Virus (BBTV), and Anthracnose.\n\n"
            "Provides ICAR-aligned treatment advisories and locates the nearest "
            "banana farming support centre."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS middleware ────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ────────────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(predict_router)

    return app


# Expose the app instance for Uvicorn
app = create_app()

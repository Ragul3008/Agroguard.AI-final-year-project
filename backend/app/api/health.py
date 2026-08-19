"""
api/health.py - Production health check for AgroGuard-AI.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.models.model_loader import ModelLoader
from app.schemas.response_schema import HealthResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Health check endpoint that verifies database connectivity and model status."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Health check: database connection failed: %s", exc)
        db_status = "disconnected"

    model_loaded = False
    try:
        ModelLoader.get_instance()
        model_loaded = True
    except Exception as exc:
        logger.warning("Health check: model not loaded: %s", exc)

    status = "ok" if db_status == "connected" and model_loaded else "degraded"
    return HealthResponse(
        status=status,
        version="2.0.0",
        model_loaded=model_loaded,
    )
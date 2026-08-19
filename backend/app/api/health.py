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
        # Check if the singleton exists without forcing it to load
        if ModelLoader._instance is not None:
            model_loaded = True
    except Exception as exc:
        logger.warning("Health check: model status check failed: %s", exc)

    status = "ok" if db_status == "connected" else "degraded"
    return HealthResponse(
        status=status,
        version="2.0.0",
        model_loaded=model_loaded,
    )
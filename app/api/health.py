"""
api/health.py - Production health check for AgroGuard-AI.
"""

from fastapi import APIRouter
from app.schemas.response_schema import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="1.1.0", model_loaded=True)
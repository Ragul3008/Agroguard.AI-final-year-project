"""
api/health.py - Health check endpoint for AgroGuard-AI.
"""

from fastapi import APIRouter
from app.schemas.response_schema import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """
    Confirms the service is running.

    Returns:
        JSON: {"status": "ok"}
    """
    return HealthResponse(status="ok")

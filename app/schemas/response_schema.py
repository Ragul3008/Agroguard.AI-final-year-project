"""
schemas/response_schema.py - Pydantic response schemas for AgroGuard-AI.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PredictResponse(BaseModel):
    """Response payload returned by POST /predict."""

    disease:        str      = Field(..., description="Detected banana disease name.")
    confidence:     float    = Field(..., ge=0.0, le=1.0, description="Model confidence score.")
    severity:       str      = Field(..., description="Severity level: Low, Medium, High, or None.")
    advisory:       str      = Field(..., description="ICAR-aligned treatment and management advice.")
    nearest_center: str      = Field(..., description="Nearest banana farming support centre.")
    timestamp:      datetime = Field(..., description="UTC timestamp of the prediction.")

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    """Response returned by GET /health."""
    status: str = Field(default="ok")


class ErrorResponse(BaseModel):
    """Standard error envelope for 4xx / 5xx responses."""
    detail: str
    code:   Optional[int] = None

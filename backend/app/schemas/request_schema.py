"""
schemas/request_schema.py - Pydantic request schemas for AgroGuard-AI.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """
    Optional metadata that accompanies the image upload in multipart/form-data.
    The image file itself is received as an UploadFile in the route handler.
    """

    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="GPS latitude of the banana farm location.",
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="GPS longitude of the banana farm location.",
    )

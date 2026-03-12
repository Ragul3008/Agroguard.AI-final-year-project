"""
api/auth.py - JWT Authentication endpoints with Rate Limiting.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.database.models import Farmer
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_farmer
from app.utils.rate_limiter import limiter
from app.utils.logger import get_logger

logger        = get_logger(__name__)
router        = APIRouter(prefix="/auth", tags=["Authentication"])
_auth_service = AuthService()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    name:     str           = Field(..., min_length=2, max_length=255, example="Ragul J")
    phone:    str           = Field(..., min_length=10, max_length=15, example="9876543210")
    password: str           = Field(..., min_length=6, example="securepassword")
    email:    Optional[str] = Field(None, example="ragul@email.com")
    village:  Optional[str] = Field(None, example="Thanjavur")
    district: Optional[str] = Field(None, example="Thanjavur")
    state:    Optional[str] = Field("Tamil Nadu", example="Tamil Nadu")


class LoginRequest(BaseModel):
    phone:    str = Field(..., example="9876543210")
    password: str = Field(..., example="securepassword")


class FarmerResponse(BaseModel):
    id:        int
    name:      str
    phone:     str
    email:     Optional[str]
    village:   Optional[str]
    district:  Optional[str]
    state:     Optional[str]
    is_active: bool

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class AuthResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   str = "30 days"
    farmer:       FarmerResponse


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new farmer account",
    description=(
        "Register with phone number and password.\n\n"
        "🛡️ **Rate limit:** 5 requests per minute per IP"
    ),
)
@limiter.limit("5/minute")
async def register(
    request:  Request,
    body:     RegisterRequest,
    db:       AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Register new farmer and return JWT token."""
    logger.info("POST /auth/register | phone='%s' name='%s'", body.phone, body.name)

    try:
        farmer = await _auth_service.register(
            db=db,
            name=body.name,
            phone=body.phone,
            password=body.password,
            email=body.email,
            village=body.village,
            district=body.district,
            state=body.state,
        )
        farmer, token = await _auth_service.login(db, body.phone, body.password)
        return AuthResponse(
            access_token=token,
            farmer=FarmerResponse.model_validate(farmer),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Registration error: %s", exc)
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with phone number and password",
    description=(
        "Login and get JWT token valid for **30 days**.\n\n"
        "🛡️ **Rate limit:** 10 requests per minute per IP"
    ),
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body:    LoginRequest,
    db:      AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Login farmer and return JWT token."""
    logger.info("POST /auth/login | phone='%s'", body.phone)

    try:
        farmer, token = await _auth_service.login(db, body.phone, body.password)
        return AuthResponse(
            access_token=token,
            farmer=FarmerResponse.model_validate(farmer),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except Exception as exc:
        logger.error("Login error: %s", exc)
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")


@router.get(
    "/me",
    response_model=FarmerResponse,
    summary="Get current farmer profile",
)
@limiter.limit("60/minute")
async def get_my_profile(
    request: Request,
    farmer:  Farmer = Depends(get_current_farmer),
) -> FarmerResponse:
    """Return current farmer's profile."""
    return FarmerResponse.model_validate(farmer)


@router.get(
    "/me/predictions",
    summary="Get my prediction history",
)
@limiter.limit("30/minute")
async def get_my_predictions(
    request: Request,
    farmer:  Farmer       = Depends(get_current_farmer),
    db:      AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return authenticated farmer's prediction history."""
    from sqlalchemy import select
    from app.database.models import Prediction

    result = await db.execute(
        select(Prediction)
        .where(Prediction.farmer_id == farmer.id)
        .order_by(Prediction.created_at.desc())
        .limit(50)
    )
    predictions = result.scalars().all()

    return [
        {
            "id":             p.id,
            "disease":        p.disease,
            "confidence_pct": p.confidence_pct,
            "severity":       p.severity,
            "is_confident":   p.is_confident,
            "nearest_center": p.nearest_center,
            "created_at":     p.created_at.isoformat() if p.created_at else None,
        }
        for p in predictions
    ]
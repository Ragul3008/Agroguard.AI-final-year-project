"""
api/auth.py - JWT Authentication endpoints with Rate Limiting.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.db import get_db
from app.database.models import Farmer
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_farmer
from app.utils.rate_limiter import limiter
from app.utils.logger import get_logger

logger        = get_logger(__name__)
settings      = get_settings()
router        = APIRouter(prefix="/auth", tags=["Authentication"])
_auth_service = AuthService()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    name:     str           = Field(..., min_length=2, max_length=255, example="Ragul J")
    phone:    str           = Field(..., min_length=10, max_length=15, example="9876543210")
    password: str           = Field(..., min_length=6, example="securepassword")
    email:    Optional[EmailStr] = Field(None, example="ragul@email.com")
    village:  Optional[str] = Field(None, example="Thanjavur")
    district: Optional[str] = Field(None, example="Thanjavur")
    state:    Optional[str] = Field("Tamil Nadu", example="Tamil Nadu")


class LoginRequest(BaseModel):
    phone:    Optional[str]      = Field(None, example="9876543210")
    email:    Optional[EmailStr] = Field(None, example="ragul@email.com")
    password: str                = Field(..., example="securepassword")


class LoginEmailRequest(BaseModel):
    email:    EmailStr = Field(..., example="ragul@email.com")
    password: str      = Field(..., example="securepassword")


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(..., description="Google ID token from frontend")


class SetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=6, example="newpassword")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token from login")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., example="farmer@example.com")


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., example="farmer@example.com")
    otp:   str      = Field(..., min_length=6, max_length=6, example="123456")
    new_password: str = Field(..., min_length=6, example="newpassword")


class FarmerResponse(BaseModel):
    id:            int
    name:          str
    phone:         Optional[str]
    email:         Optional[str]
    village:       Optional[str]
    district:      Optional[str]
    state:         Optional[str]
    is_active:     bool
    auth_provider: str

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class AuthResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    str = "15 minutes"
    farmer:        FarmerResponse


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    str = "15 minutes"


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
    """Register new farmer and return JWT access + refresh tokens."""
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
        farmer, access_token, refresh_token = await _auth_service.login(db, body.phone, body.password)
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
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
    summary="Login with phone number or email and password",
    description=(
        "Login and get JWT access token (15 min) + refresh token (30 days).\n\n"
        "🛡️ **Rate limit:** 10 requests per minute per IP"
    ),
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body:    LoginRequest,
    db:      AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Login farmer and return JWT access + refresh tokens."""
    if body.phone:
        logger.info("POST /auth/login | phone='%s'", body.phone)
        try:
            farmer, access_token, refresh_token = await _auth_service.login(db, body.phone, body.password)
            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                farmer=FarmerResponse.model_validate(farmer),
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
        except Exception as exc:
            logger.error("Login error: %s", exc)
            raise HTTPException(status_code=500, detail="Login failed. Please try again.")
    elif body.email:
        logger.info("POST /auth/login | email='%s'", body.email)
        try:
            farmer, access_token, refresh_token = await _auth_service.login_with_email(db, body.email, body.password)
            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                farmer=FarmerResponse.model_validate(farmer),
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
        except Exception as exc:
            logger.error("Login error: %s", exc)
            raise HTTPException(status_code=500, detail="Login failed. Please try again.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide either phone number or email.")


@router.post(
    "/login/email",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description=(
        "Login with email instead of phone number.\n\n"
        "🛡️ **Rate limit:** 10 requests per minute per IP"
    ),
)
@limiter.limit("10/minute")
async def login_email(
    request: Request,
    body:    LoginEmailRequest,
    db:      AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Login farmer with email and return JWT access + refresh tokens."""
    logger.info("POST /auth/login/email | email='%s'", body.email)

    try:
        farmer, access_token, refresh_token = await _auth_service.login_with_email(db, body.email, body.password)
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            farmer=FarmerResponse.model_validate(farmer),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except Exception as exc:
        logger.error("Email login error: %s", exc)
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")


@router.post(
    "/google",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in with Google (OAuth2 ID token)",
    description=(
        "Accepts a Google ID token from the frontend, verifies it with Google's public keys, "
        "and either links to an existing account (by email) or creates a new Google-only account. "
        "Returns JWT access + refresh tokens.\n\n"
        "🛡️ **Rate limit:** 10 requests per minute per IP"
    ),
)
@limiter.limit("10/minute")
async def google_login(
    request: Request,
    body:    GoogleLoginRequest,
    db:      AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Google OAuth2 login - verify ID token and issue JWT tokens."""
    logger.info("POST /auth/google")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests

        try:
            # Verify the token
            claims = id_token.verify_oauth2_token(
                body.id_token,
                requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )
        except ValueError as exc:
            logger.warning("Google ID token validation failed: %s", exc)
            raise HTTPException(status_code=401, detail="Invalid Google ID token")

        # Extract user info from verified token
        google_id = claims.get("sub")
        email = claims.get("email")
        name = claims.get("name", "Google User")

        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Google token missing required claims")

        farmer, access_token, refresh_token = await _auth_service.google_login(
            db=db,
            google_id=google_id,
            email=email,
            name=name,
        )
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            farmer=FarmerResponse.model_validate(farmer),
        )
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Google login ValueError: %r", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        import traceback
        logger.error("Google login error: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Google login failed. Please try again.")


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using refresh token",
    description=(
        "Exchange a valid refresh token for a new access + refresh token pair. "
        "Implements refresh token rotation (old refresh token is invalidated).\n\n"
        "🛡️ **Rate limit:** 30 requests per minute per IP"
    ),
)
@limiter.limit("30/minute")
async def refresh_tokens(
    request: Request,
    body:    RefreshRequest,
    db:      AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token (rotation)."""
    logger.info("POST /auth/refresh")

    try:
        access_token, refresh_token = await _auth_service.refresh_tokens(db, body.refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except Exception as exc:
        logger.error("Token refresh error: %s", exc)
        raise HTTPException(status_code=500, detail="Token refresh failed. Please login again.")


@router.post(
    "/set-password",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Set password for Google-only account",
    description=(
        "Allows a farmer who signed up via Google to set a password, "
        "enabling password-based login in addition to Google.\n\n"
        "🛡️ **Rate limit:** 5 requests per minute per IP"
    ),
)
@limiter.limit("5/minute")
async def set_password(
    request: Request,
    body:    SetPasswordRequest,
    db:      AsyncSession = Depends(get_db),
    farmer:  Farmer = Depends(get_current_farmer),
) -> AuthResponse:
    """Set password for Google-only account."""
    logger.info("POST /auth/set-password | farmer_id=%d", farmer.id)

    try:
        farmer = await _auth_service.set_password(db, farmer.id, body.password)
        access_token, refresh_token = _auth_service.create_token_pair(farmer.id, farmer.phone or farmer.email)
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            farmer=FarmerResponse.model_validate(farmer),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Set password error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to set password. Please try again.")


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset OTP via email",
    description=(
        "Sends a 6-digit OTP to the registered email for password reset. "
        "Always returns success to prevent email enumeration.\n\n"
        "🛡️ **Rate limit:** 3 requests per 15 minutes per email/IP"
    ),
)
@limiter.limit("3/15minutes")
async def forgot_password(
    request: Request,
    body:    ForgotPasswordRequest,
    db:      AsyncSession = Depends(get_db),
) -> dict:
    """Request password reset OTP. Always returns generic success message."""
    logger.info("POST /auth/forgot-password | email='%s'", body.email)

    try:
        # Always return success to prevent email enumeration
        await _auth_service.request_password_reset(db, body.email)
        return {
            "message": "If an account with that email exists, a password reset OTP has been sent."
        }
    except Exception as exc:
        logger.error("Forgot password error: %s", exc)
        # Still return generic success to prevent enumeration
        return {
            "message": "If an account with that email exists, a password reset OTP has been sent."
        }


@router.post(
    "/reset-password",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password using OTP",
    description=(
        "Reset password using the 6-digit OTP received via email.\n\n"
        "🛡️ **Rate limit:** 10 requests per minute per IP"
    ),
)
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    body:    ResetPasswordRequest,
    db:      AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Reset password using OTP and return new JWT tokens."""
    logger.info("POST /auth/reset-password | email='%s'", body.email)

    try:
        farmer = await _auth_service.reset_password(db, body.email, body.otp, body.new_password)
        access_token, refresh_token = _auth_service.create_token_pair(farmer.id, farmer.phone or farmer.email)
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            farmer=FarmerResponse.model_validate(farmer),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Reset password error: %s", exc)
        raise HTTPException(status_code=500, detail="Password reset failed. Please try again.")


class UpdateProfileRequest(BaseModel):
    name:     Optional[str] = Field(None, example="New Name")
    village:  Optional[str] = Field(None, example="New Village")
    district: Optional[str] = Field(None, example="New District")
    state:    Optional[str] = Field(None, example="Tamil Nadu")

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


@router.put(
    "/me",
    response_model=FarmerResponse,
    summary="Update current farmer profile",
)
@limiter.limit("30/minute")
async def update_my_profile(
    request: Request,
    body:    UpdateProfileRequest,
    farmer:  Farmer       = Depends(get_current_farmer),
    db:      AsyncSession = Depends(get_db),
) -> FarmerResponse:
    """Update authenticated farmer's profile details."""
    updated_farmer = await _auth_service.update_profile(
        db=db,
        farmer_id=farmer.id,
        update_data=body.model_dump(exclude_unset=True)
    )
    return FarmerResponse.model_validate(updated_farmer)


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
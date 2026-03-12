"""
services/auth_service.py - JWT Authentication service for AgroGuard-AI.

Features:
    - Farmer registration with bcrypt password hashing
    - JWT token generation and verification
    - Phone number as primary login identifier
    - Token expiry: 30 days (farmer-friendly)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import Farmer
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# JWT settings
# ---------------------------------------------------------------------------
_ALGORITHM       = "HS256"
_TOKEN_EXPIRE_DAYS = 30   # Farmers stay logged in for 30 days


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


def create_access_token(farmer_id: int, phone: str) -> str:
    """
    Generate a JWT access token for a farmer.

    Args:
        farmer_id: Farmer's database ID.
        phone:     Farmer's phone number.

    Returns:
        Signed JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub":       str(farmer_id),
        "phone":     phone,
        "exp":       expire,
        "iat":       datetime.now(timezone.utc),
        "token_type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)
    logger.info("JWT token created for farmer_id=%d", farmer_id)
    return token


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Returns:
        Payload dict if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
        return payload
    except JWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        return None


class AuthService:
    """Handles farmer registration and authentication."""

    async def register(
        self,
        db:       AsyncSession,
        name:     str,
        phone:    str,
        password: str,
        email:    Optional[str] = None,
        village:  Optional[str] = None,
        district: Optional[str] = None,
        state:    Optional[str] = "Tamil Nadu",
    ) -> Farmer:
        """
        Register a new farmer account.

        Args:
            db:       Async database session.
            name:     Farmer's full name.
            phone:    Farmer's phone number (used for login).
            password: Plain text password (will be hashed).
            email:    Optional email address.
            village:  Optional village name.
            district: Optional district name.
            state:    State (default: Tamil Nadu).

        Returns:
            Newly created Farmer ORM object.

        Raises:
            ValueError: If phone number already registered.
        """
        # Check if phone already exists
        existing = await db.execute(
            select(Farmer).where(Farmer.phone == phone)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Phone number {phone} is already registered.")

        farmer = Farmer(
            name          = name,
            phone         = phone,
            email         = email,
            password_hash = hash_password(password),
            village       = village,
            district      = district,
            state         = state,
        )
        db.add(farmer)
        await db.commit()
        await db.refresh(farmer)

        logger.info("New farmer registered → id=%d name='%s' phone='%s'",
                    farmer.id, farmer.name, farmer.phone)
        return farmer

    async def login(
        self,
        db:       AsyncSession,
        phone:    str,
        password: str,
    ) -> tuple[Farmer, str]:
        """
        Authenticate farmer and return JWT token.

        Args:
            db:       Async database session.
            phone:    Farmer's phone number.
            password: Plain text password.

        Returns:
            Tuple of (Farmer, jwt_token).

        Raises:
            ValueError: If credentials are invalid.
        """
        result = await db.execute(
            select(Farmer).where(Farmer.phone == phone)
        )
        farmer = result.scalar_one_or_none()

        if not farmer:
            raise ValueError("Invalid phone number or password.")

        if not farmer.is_active:
            raise ValueError("Account is deactivated. Contact support.")

        if not verify_password(password, farmer.password_hash):
            raise ValueError("Invalid phone number or password.")

        token = create_access_token(farmer.id, farmer.phone)
        logger.info("Farmer logged in → id=%d phone='%s'", farmer.id, farmer.phone)
        return farmer, token

    async def get_farmer_by_id(
        self,
        db:        AsyncSession,
        farmer_id: int,
    ) -> Optional[Farmer]:
        """Retrieve farmer by ID."""
        result = await db.execute(
            select(Farmer).where(Farmer.id == farmer_id)
        )
        return result.scalar_one_or_none()
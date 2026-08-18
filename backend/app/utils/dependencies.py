"""
utils/dependencies.py - FastAPI JWT authentication dependencies.

Usage:
    from app.utils.dependencies import get_current_farmer

    @router.get("/protected")
    async def protected_route(farmer: Farmer = Depends(get_current_farmer)):
        return {"message": f"Hello {farmer.name}"}
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.database.models import Farmer
from app.services.auth_service import AuthService, decode_access_token
from app.utils.logger import get_logger

logger = get_logger(__name__)

_bearer_scheme = HTTPBearer()
_auth_service  = AuthService()


async def get_current_farmer(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Farmer:
    """
    FastAPI dependency — extracts and validates JWT token.

    Returns the authenticated Farmer if token is valid.
    Raises HTTP 401 if token is missing, invalid, or expired.

    Usage:
        farmer: Farmer = Depends(get_current_farmer)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        logger.warning("Invalid JWT token received.")
        raise credentials_exception

    farmer_id = payload.get("sub")
    if farmer_id is None:
        raise credentials_exception

    farmer = await _auth_service.get_farmer_by_id(db, int(farmer_id))
    if farmer is None or not farmer.is_active:
        raise credentials_exception

    return farmer


async def get_optional_farmer(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Farmer | None:
    """
    Optional JWT dependency — returns farmer if token provided, None otherwise.
    Use for endpoints that work both authenticated and unauthenticated.
    """
    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None

    farmer_id = payload.get("sub")
    if farmer_id is None:
        return None

    return await _auth_service.get_farmer_by_id(db, int(farmer_id))
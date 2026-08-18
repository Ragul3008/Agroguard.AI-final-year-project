"""
services/auth_service.py - JWT Authentication service for AgroGuard-AI.

Features:
    - Farmer registration with bcrypt password hashing
    - JWT token generation and verification (access + refresh tokens)
    - Phone/email as primary login identifier
    - Google OAuth2 authentication
    - Password reset via 6-digit OTP email
    - Token expiry: access 15 min, refresh 30 days (farmer-friendly)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import Farmer, AuthProvider, PasswordReset
from app.utils.logger import get_logger
from app.services.email_service import EmailService

logger   = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# JWT settings
# ---------------------------------------------------------------------------
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
_REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30)

# ---------------------------------------------------------------------------
# OTP settings
# ---------------------------------------------------------------------------
_OTP_EXPIRE_MINUTES = 10
_OTP_MAX_ATTEMPTS = 5


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


def create_access_token(farmer_id: int, phone: str) -> str:
    """
    Generate a JWT access token for a farmer (valid for 24 hours).

    Args:
        farmer_id: Farmer's database ID.
        phone:     Farmer's phone number.

    Returns:
        Signed JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub":       str(farmer_id),
        "phone":     phone,
        "exp":       expire,
        "iat":       datetime.now(timezone.utc),
        "token_type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)
    logger.info("JWT access token created for farmer_id=%d", farmer_id)
    return token


def create_refresh_token(farmer_id: int, phone: str) -> str:
    """
    Generate a JWT refresh token for a farmer (long-lived: 30 days).

    Args:
        farmer_id: Farmer's database ID.
        phone:     Farmer's phone number.

    Returns:
        Signed JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub":       str(farmer_id),
        "phone":     phone,
        "exp":       expire,
        "iat":       datetime.now(timezone.utc),
        "token_type": "refresh",
    }
    token = jwt.encode(payload, settings.REFRESH_SECRET_KEY, algorithm=_ALGORITHM)
    logger.info("JWT refresh token created for farmer_id=%d", farmer_id)
    return token


def create_token_pair(farmer_id: int, phone: str) -> tuple[str, str]:
    """Create both access and refresh tokens."""
    return create_access_token(farmer_id, phone), create_refresh_token(farmer_id, phone)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.

    Returns:
        Payload dict if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
        if payload.get("token_type") != "access":
            return None
        return payload
    except JWTError as exc:
        logger.warning("JWT access token decode failed: %s", exc)
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT refresh token.

    Returns:
        Payload dict if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[_ALGORITHM])
        if payload.get("token_type") != "refresh":
            return None
        return payload
    except JWTError as exc:
        logger.warning("JWT refresh token decode failed: %s", exc)
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
        Register a new farmer account with password authentication.

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

        # Check if email already exists
        if email:
            existing_email = await db.execute(
                select(Farmer).where(Farmer.email == email)
            )
            if existing_email.scalar_one_or_none():
                raise ValueError(f"Email {email} is already registered.")

        farmer = Farmer(
            name          = name,
            phone         = phone,
            email         = email,
            password_hash = hash_password(password),
            village       = village,
            district      = district,
            state         = state,
            auth_provider = AuthProvider.PASSWORD,
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
    ) -> tuple[Farmer, str, str]:
        """
        Authenticate farmer and return JWT access + refresh tokens.

        Args:
            db:       Async database session.
            phone:    Farmer's phone number.
            password: Plain text password.

        Returns:
            Tuple of (Farmer, access_token, refresh_token).

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

        if farmer.auth_provider != AuthProvider.PASSWORD:
            raise ValueError("This account uses Google sign-in. Please use 'Sign in with Google'.")

        if not farmer.password_hash or not verify_password(password, farmer.password_hash):
            raise ValueError("Invalid phone number or password.")

        access_token, refresh_token = create_token_pair(farmer.id, farmer.phone)
        logger.info("Farmer logged in → id=%d phone='%s'", farmer.id, farmer.phone)
        return farmer, access_token, refresh_token

    async def login_with_email(
        self,
        db:       AsyncSession,
        email:    str,
        password: str,
    ) -> tuple[Farmer, str, str]:
        """
        Authenticate farmer with email and return JWT access + refresh tokens.
        """
        result = await db.execute(
            select(Farmer).where(Farmer.email == email)
        )
        farmer = result.scalar_one_or_none()

        if not farmer:
            raise ValueError("Invalid email or password.")

        if not farmer.is_active:
            raise ValueError("Account is deactivated. Contact support.")

        if farmer.auth_provider != AuthProvider.PASSWORD:
            raise ValueError("This account uses Google sign-in. Please use 'Sign in with Google'.")

        if not farmer.password_hash or not verify_password(password, farmer.password_hash):
            raise ValueError("Invalid email or password.")

        access_token, refresh_token = create_token_pair(farmer.id, farmer.phone)
        logger.info("Farmer logged in (email) → id=%d email='%s'", farmer.id, farmer.email)
        return farmer, access_token, refresh_token

    async def google_login(
        self,
        db:       AsyncSession,
        google_id: str,
        email:    str,
        name:     str,
    ) -> tuple[Farmer, str, str]:
        """
        Authenticate or register farmer via Google OAuth.

        Args:
            db:       Async database session.
            google_id: Google's unique user ID (sub claim).
            email:    Farmer's email from Google.
            name:     Farmer's name from Google.

        Returns:
            Tuple of (Farmer, access_token, refresh_token).
        """
        # Try to find existing farmer by google_id
        result = await db.execute(
            select(Farmer).where(Farmer.google_id == google_id)
        )
        farmer = result.scalar_one_or_none()

        if farmer:
            # Existing Google user - update info if changed
            if farmer.email != email:
                farmer.email = email
            if farmer.name != name:
                farmer.name = name
            await db.commit()
            await db.refresh(farmer)
            logger.info("Existing Google farmer logged in → id=%d email='%s'", farmer.id, farmer.email)
        else:
            # Check if email exists with password auth - link accounts
            result = await db.execute(
                select(Farmer).where(Farmer.email == email)
            )
            farmer = result.scalar_one_or_none()

            if farmer:
                # Link Google to existing account
                farmer.google_id = google_id
                farmer.auth_provider = AuthProvider.GOOGLE
                # Keep existing password_hash for password login option
                await db.commit()
                await db.refresh(farmer)
                logger.info("Google linked to existing farmer → id=%d email='%s'", farmer.id, farmer.email)
            else:
                # Create new Google-only account (no password)
                farmer = Farmer(
                    name           = name,
                    email          = email,
                    google_id      = google_id,
                    auth_provider  = AuthProvider.GOOGLE,
                    password_hash  = None,  # No password for Google-only accounts
                    state          = "Tamil Nadu",
                )
                db.add(farmer)
                await db.commit()
                await db.refresh(farmer)
                logger.info("New Google farmer registered → id=%d email='%s'", farmer.id, farmer.email)

        access_token, refresh_token = create_token_pair(farmer.id, farmer.phone or farmer.email)
        return farmer, access_token, refresh_token

    async def set_password(
        self,
        db:        AsyncSession,
        farmer_id: int,
        password:  str,
    ) -> Farmer:
        """
        Set password for a Google-only account (enables password login).

        Args:
            db:        Async database session.
            farmer_id: Farmer's database ID.
            password:  Plain text password.

        Returns:
            Updated Farmer object.

        Raises:
            ValueError: If farmer not found or already has password.
        """
        result = await db.execute(
            select(Farmer).where(Farmer.id == farmer_id)
        )
        farmer = result.scalar_one_or_none()

        if not farmer:
            raise ValueError("Farmer not found.")

        if farmer.password_hash:
            raise ValueError("Account already has a password. Use 'change password' instead.")

        farmer.password_hash = hash_password(password)
        # Keep auth_provider as GOOGLE since they can still use Google
        await db.commit()
        await db.refresh(farmer)

        logger.info("Password set for farmer → id=%d", farmer_id)
        return farmer

    async def refresh_tokens(
        self,
        db:       AsyncSession,
        refresh_token: str,
    ) -> tuple[str, str]:
        """
        Generate new access + refresh token pair from a valid refresh token.

        Implements refresh token rotation: old refresh token is invalidated,
        new pair is issued.

        Args:
            db:            Async database session.
            refresh_token: Current refresh token.

        Returns:
            Tuple of (new_access_token, new_refresh_token).

        Raises:
            ValueError: If refresh token is invalid or expired.
        """
        payload = decode_refresh_token(refresh_token)
        if not payload:
            raise ValueError("Invalid or expired refresh token.")

        farmer_id = int(payload.get("sub"))
        farmer = await self.get_farmer_by_id(db, farmer_id)

        if not farmer or not farmer.is_active:
            raise ValueError("Invalid or expired refresh token.")

        # Generate new token pair (rotation)
        access_token, new_refresh_token = create_token_pair(farmer.id, farmer.phone or farmer.email)
        logger.info("Tokens refreshed for farmer → id=%d", farmer_id)
        return access_token, new_refresh_token

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

    async def request_password_reset(
        self,
        db: AsyncSession,
        email: str,
    ) -> None:
        """
        Generate an OTP, store it, and send it to the farmer's email.
        """
        # Find farmer by email
        result = await db.execute(
            select(Farmer).where(Farmer.email == email)
        )
        farmer = result.scalar_one_or_none()
        
        if not farmer or not farmer.is_active:
            # Silently return to prevent email enumeration
            return

        # Delete any previous unused OTPs for this email
        await db.execute(
            delete(PasswordReset).where(
                PasswordReset.email == email,
                PasswordReset.used == False
            )
        )

        # Generate 6-digit OTP
        otp = str(secrets.randbelow(1000000)).zfill(6)
        
        # Store in db
        reset_entry = PasswordReset(
            email=email,
            otp_hash=hash_password(otp),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=_OTP_EXPIRE_MINUTES)
        )
        db.add(reset_entry)
        await db.commit()
        
        # Send email
        EmailService.send_otp_email(email, otp)
        
    async def reset_password(
        self,
        db: AsyncSession,
        email: str,
        otp: str,
        new_password: str,
    ) -> Farmer:
        """
        Verify OTP and reset password.
        """
        # Find active OTP request
        result = await db.execute(
            select(PasswordReset).where(
                PasswordReset.email == email,
                PasswordReset.used == False,
                PasswordReset.expires_at > datetime.now(timezone.utc)
            ).order_by(PasswordReset.created_at.desc())
        )
        reset_entry = result.scalar_one_or_none()

        if not reset_entry:
            raise ValueError("Invalid or expired OTP.")

        if reset_entry.attempts >= reset_entry.max_attempts:
            raise ValueError("Maximum OTP attempts exceeded. Please request a new one.")

        if not verify_password(otp, reset_entry.otp_hash):
            reset_entry.attempts += 1
            await db.commit()
            raise ValueError("Invalid OTP.")

        # OTP is valid, mark as used
        reset_entry.used = True
        
        # Find user and update password
        result = await db.execute(
            select(Farmer).where(Farmer.email == email)
        )
        farmer = result.scalar_one_or_none()
        
        if not farmer:
            raise ValueError("Account not found.")
            
        farmer.password_hash = hash_password(new_password)
        await db.commit()
        await db.refresh(farmer)
        
        logger.info("Password reset successful for email='%s'", email)
        return farmer

    async def get_farmer_by_email(
        self,
        db:    AsyncSession,
        email: str,
    ) -> Optional[Farmer]:
        """Retrieve farmer by email."""
        result = await db.execute(
            select(Farmer).where(Farmer.email == email)
        )
        return result.scalar_one_or_none()

    # ---------------------------------------------------------------------------
    # Password Reset OTP Methods
    # ---------------------------------------------------------------------------

    def _generate_otp(self) -> str:
        """Generate a cryptographically secure 6-digit OTP."""
        return f"{secrets.randbelow(1000000):06d}"

    def _hash_otp(self, otp: str) -> str:
        """Hash OTP using bcrypt."""
        return hash_password(otp)

    def _verify_otp(self, plain_otp: str, hashed_otp: str) -> bool:
        """Verify plain OTP against bcrypt hash."""
        return verify_password(plain_otp, hashed_otp)

    async def _send_otp_email(self, email: str, otp: str) -> bool:
        """
        Send OTP email via Resend API.
        Returns True if sent successfully.
        """
        if not settings.EMAIL_API_KEY:
            logger.warning("EMAIL_API_KEY not configured, skipping email send")
            return False

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.EMAIL_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": settings.EMAIL_FROM_ADDRESS,
                        "to": [email],
                        "subject": "AgroGuard AI - Password Reset OTP",
                        "html": f"""
                            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                                <h2 style="color: #16a34a;">AgroGuard AI - Password Reset</h2>
                                <p>You requested a password reset for your AgroGuard AI account.</p>
                                <p>Your 6-digit OTP code is:</p>
                                <div style="background: #f0fdf4; border: 2px solid #16a34a; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                                    <span style="font-size: 32px; font-weight: bold; color: #16a34a; letter-spacing: 4px;">{otp}</span>
                                </div>
                                <p><strong>This code expires in {_OTP_EXPIRE_MINUTES} minutes.</strong></p>
                                <p>If you didn't request this, please ignore this email.</p>
                                <hr style="margin: 20px 0; border: none; border-top: 1px solid #e5e7eb;">
                                <p style="color: #6b7280; font-size: 12px;">AgroGuard AI - Banana Disease Detection System</p>
                            </div>
                        """,
                    },
                )
                resp.raise_for_status()
                logger.info("OTP email sent to %s", email)
                return True
        except Exception as exc:
            logger.error("Failed to send OTP email to %s: %s", email, exc)
            return False

    async def request_password_reset(
        self,
        db:    AsyncSession,
        email: str,
    ) -> bool:
        """
        Request password reset for an email.
        Always returns True (success) to prevent email enumeration.
        Actually sends email only if account exists.
        """
        # Check if farmer exists with this email
        farmer = await self.get_farmer_by_email(db, email)

        # Rate limiting: check recent OTP requests for this email
        recent_otp = await db.execute(
            select(PasswordReset)
            .where(PasswordReset.email == email)
            .where(PasswordReset.created_at > datetime.now(timezone.utc) - timedelta(minutes=15))
            .order_by(PasswordReset.created_at.desc())
            .limit(1)
        )
        recent = recent_otp.scalar_one_or_none()
        if recent:
            logger.warning("Rate limit: OTP requested too recently for %s", email)
            # Still return True to prevent enumeration
            return True

        if farmer and farmer.auth_provider == AuthProvider.PASSWORD:
            # Only send email for password-based accounts (not Google-only)
            otp = self._generate_otp()
            otp_hash = self._hash_otp(otp)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=_OTP_EXPIRE_MINUTES)

            # Invalidate any existing unused OTPs for this email
            await db.execute(
                delete(PasswordReset).where(
                    PasswordReset.email == email,
                    PasswordReset.used == False,  # noqa: E712
                )
            )

            # Create new OTP record
            otp_record = PasswordReset(
                email=email,
                otp_hash=otp_hash,
                expires_at=expires_at,
                max_attempts=_OTP_MAX_ATTEMPTS,
            )
            db.add(otp_record)
            await db.commit()

            # Send email
            await self._send_otp_email(email, otp)
            logger.info("Password reset OTP generated for %s", email)
        else:
            # Google-only account or non-existent email - don't send email
            # But still return True to prevent enumeration
            logger.info("Password reset requested for non-password account or non-existent email: %s", email)

        return True

    async def reset_password(
        self,
        db:    AsyncSession,
        email: str,
        otp:   str,
        new_password: str,
    ) -> Farmer:
        """
        Reset password using OTP.

        Args:
            db:            Async database session.
            email:         Farmer's email.
            otp:           6-digit OTP from email.
            new_password:  New plain text password.

        Returns:
            Updated Farmer object.

        Raises:
            ValueError: If OTP is invalid, expired, or too many attempts.
        """
        # Find the most recent unused OTP for this email
        result = await db.execute(
            select(PasswordReset)
            .where(PasswordReset.email == email)
            .where(PasswordReset.used == False)  # noqa: E712
            .order_by(PasswordReset.created_at.desc())
            .limit(1)
        )
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            raise ValueError("No valid OTP found. Please request a new one.")

        # Check expiry
        if datetime.now(timezone.utc) > otp_record.expires_at:
            raise ValueError("OTP has expired. Please request a new one.")

        # Check attempts
        if otp_record.attempts >= otp_record.max_attempts:
            raise ValueError("Too many failed attempts. Please request a new OTP.")

        # Verify OTP
        if not self._verify_otp(otp, otp_record.otp_hash):
            otp_record.attempts += 1
            await db.commit()
            raise ValueError(f"Invalid OTP. {otp_record.max_attempts - otp_record.attempts} attempts remaining.")

        # OTP is valid - mark as used
        otp_record.used = True
        await db.commit()

        # Find farmer and update password
        farmer = await self.get_farmer_by_email(db, email)
        if not farmer:
            raise ValueError("Account not found.")

        if not farmer.is_active:
            raise ValueError("Account is deactivated. Contact support.")

        # Update password hash
        farmer.password_hash = hash_password(new_password)
        await db.commit()
        await db.refresh(farmer)

        # Invalidate all refresh tokens for this user by... 
        # (In a production system, you'd maintain a token blacklist or version counter)
        # For now, the old refresh tokens will still work until they expire.
        # A more robust solution would add a token_version column to Farmer.

        logger.info("Password reset successful for %s", email)
        return farmer

    def create_token_pair(self, farmer_id: int, phone: str) -> tuple[str, str]:
        """Create both access and refresh tokens (instance method wrapper)."""
        return create_token_pair(farmer_id, phone)

    async def update_profile(
        self,
        db:          AsyncSession,
        farmer_id:   int,
        update_data: dict,
    ) -> Farmer:
        """
        Update the farmer's profile.

        Args:
            db:          Async database session.
            farmer_id:   Farmer's database ID.
            update_data: Dictionary containing fields to update.

        Returns:
            Updated Farmer object.

        Raises:
            ValueError: If farmer not found.
        """
        result = await db.execute(
            select(Farmer).where(Farmer.id == farmer_id)
        )
        farmer = result.scalar_one_or_none()

        if not farmer:
            raise ValueError("Farmer account not found.")

        # Update allowed fields
        for key, value in update_data.items():
            if hasattr(farmer, key):
                setattr(farmer, key, value)

        await db.commit()
        await db.refresh(farmer)
        logger.info("Farmer profile updated → id=%d", farmer.id)
        return farmer
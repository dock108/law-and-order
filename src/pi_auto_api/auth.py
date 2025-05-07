"""Authentication utilities for Staff users using JWT."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from pi_auto.db.crud import get_staff_by_email  # Corrected import path
from pi_auto.db.models import Staff  # Corrected import path
from pi_auto.db.session import get_db  # Corrected import path, assuming location

# Assuming your models and config are structured like this
# Adjust imports as per your project structure
from pi_auto_api.config import settings

logger = logging.getLogger(__name__)

# Passlib context for password hashing (using bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer scheme
# tokenUrl should point to your login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Helper Pydantic model for token data structure (optional but good practice)
class TokenData(BaseModel):  # BaseModel is imported from Pydantic
    """Schema for data stored within the JWT token payload."""

    email: Optional[EmailStr] = None
    # You can add other fields like user_id (sub) if needed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token.

    Args:
        data: Dictionary containing the claims for the token (e.g., sub, email, role).
        expires_delta: Optional timedelta for token expiration.
                       Defaults to JWT_EXP_MINUTES from settings.

    Returns:
        The encoded JWT string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXP_MINUTES
        )
    to_encode.update({"exp": expire})

    if not settings.JWT_SECRET:
        logger.error("JWT_SECRET not configured. Cannot create access token.")
        raise ValueError("JWT_SECRET is not set in the application settings.")

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm="HS256",  # Algorithm as per prompt
    )
    return encoded_jwt


async def get_current_staff(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Staff:
    """Dependency to get the current authenticated staff member from a JWT.

    Decodes the JWT, validates its claims, and retrieves the staff user
    from the database.

    Args:
        token: The JWT token from the Authorization header.
        db: Database session dependency.

    Raises:
        HTTPException (401): If the token is invalid, expired, or the user
                             is not found or not active.

    Returns:
        The authenticated and active Staff user model instance.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not settings.JWT_SECRET:
        logger.error("JWT_SECRET not configured. Cannot validate token.")
        raise credentials_exception  # Or a 500 error

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],  # Algorithm as per prompt
        )
        # The prompt specifies JWT {sub: staff_id, email, role:'staff', exp: …}
        # We'll primarily use email to fetch the user as per common practice.
        email: Optional[str] = payload.get("email")
        if email is None:
            logger.warning(f"Email not found in JWT payload: {payload}")
            raise credentials_exception
        # Validate email format if needed, jose-jwt might not do this for custom claims
        # token_data = TokenData(email=email_from_payload)  # Pydantic validation
    except JWTError as e:
        logger.warning(f"JWT decoding/validation error: {e}")
        raise credentials_exception from e
    except ValidationError as e:  # If using Pydantic model for payload validation
        logger.warning(f"JWT payload validation error: {e}")
        raise credentials_exception from e

    staff_user = await get_staff_by_email(db, email=email)

    if staff_user is None:
        logger.warning(f"Staff user with email '{email}' from JWT not found in DB.")
        raise credentials_exception
    if not staff_user.is_active:
        logger.warning(f"Staff user '{email}' from JWT is inactive.")
        raise HTTPException(  # Specific error for inactive user
            status_code=status.HTTP_401_UNAUTHORIZED,  # Or 403 Forbidden
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return staff_user


# Note: Ensure `get_staff_by_email` is implemented in your crud.py
# and `get_db` is available in session.py or similar.
# Also, TokenData needs pydantic.BaseModel. If you don't have a shared BaseModel,
# import it from pydantic directly.

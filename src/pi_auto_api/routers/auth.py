"""API Router for authentication related endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

# from fastapi.security import OAuth2PasswordRequestForm # For {email, pwd} form
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

# from pi_auto_api.config import settings # If needed for direct settings access
from pi_auto.db.crud import get_staff_by_email

# from pi_auto.db.models import Staff # Will be used by protected routes elsewhere
from pi_auto.db.session import get_db
from pi_auto_api.auth import (
    create_access_token,
    # get_current_staff, # Will be used by protected routes elsewhere
    verify_password,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class Token(BaseModel):
    """Response model for JWT token."""

    access_token: str
    token_type: str


# The prompt specifies body {email, password}, so we use a Pydantic model.
class StaffLoginRequest(BaseModel):
    """Request model for staff login with JSON body."""

    email: EmailStr
    password: str


@router.post("/login", response_model=Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: StaffLoginRequest,  # Correct way to receive JSON body
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """Logs in a staff user and returns an access token."""
    staff_user = await get_staff_by_email(db, email=form_data.email)
    if not staff_user or not staff_user.is_active:
        logger.warning(
            f"Login attempt for non-existent or inactive email: {form_data.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",  # Generic message for security
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, staff_user.hashed_password):
        logger.warning(f"Invalid password attempt for email: {form_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",  # Generic message for security
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT
    # Prompt: JWT {sub: staff_id, email, role:'staff', exp: …}
    access_token_data = {
        "sub": str(staff_user.id),  # subject is typically user ID
        "email": staff_user.email,
        "role": "staff",  # Assuming a single role 'staff' for now
        # 'exp' is handled by create_access_token
    }
    access_token = create_access_token(data=access_token_data)

    return {"access_token": access_token, "token_type": "bearer"}


# Example of a protected route (can be in another router file)
# from pi_auto_api.db.models import Staff # already imported
# @router.get("/users/me", response_model=Staff, tags=["Authentication"])
# async def read_users_me(current_user: Staff = Depends(get_current_staff)):
#     return current_user

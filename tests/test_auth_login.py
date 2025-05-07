"""Tests for staff JWT authentication and login endpoint."""

import pytest
from httpx import AsyncClient
from jose import jwt  # For decoding token in tests

from pi_auto.db.models import Staff

# from sqlalchemy.ext.asyncio import AsyncSession # No longer needed here
# from pi_auto_api.auth import get_password_hash # Moved to conftest
from pi_auto_api.config import settings

# Assuming fixtures are defined in conftest:
# async_client, db_session, test_staff_user, inactive_test_staff_user

# Constants for testing (can potentially move to conftest too if shared more widely)
TEST_STAFF_EMAIL = "test.staff@example.com"
TEST_STAFF_PASSWORD = "TestPassword123!"

# Fixture definitions removed - moved to conftest.py


@pytest.mark.asyncio
async def test_login_happy_path(async_client: AsyncClient, test_staff_user: Staff):
    """Test successful login and token validation."""
    response = await async_client.post(
        "/auth/login", json={"email": TEST_STAFF_EMAIL, "password": TEST_STAFF_PASSWORD}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Decode token to verify claims
    assert settings.JWT_SECRET is not None, "JWT_SECRET must be set for testing"
    payload = jwt.decode(
        token_data["access_token"], settings.JWT_SECRET, algorithms=["HS256"]
    )

    assert payload["email"] == TEST_STAFF_EMAIL
    assert payload["sub"] == str(test_staff_user.id)
    assert payload["role"] == "staff"


@pytest.mark.asyncio
async def test_login_inactive_user(
    async_client: AsyncClient, inactive_test_staff_user: Staff
):
    """Test login attempt for an inactive user."""
    response = await async_client.post(
        "/auth/login",
        json={"email": "inactive.staff@example.com", "password": "anotherpassword"},
    )
    assert response.status_code == 401
    # Based on the login route, the detail is generic for non-existent/inactive
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, test_staff_user: Staff):
    """Test login attempt with wrong password."""
    response = await async_client.post(
        "/auth/login", json={"email": TEST_STAFF_EMAIL, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_non_existent_user(async_client: AsyncClient):
    """Test login attempt for a non-existent user."""
    response = await async_client.post(
        "/auth/login",
        json={"email": "no.such.user@example.com", "password": "anypassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_protected_route_no_token(async_client: AsyncClient):
    """Test accessing a protected route without a token."""
    # Assuming /api/cases is a protected route from pi_workflow.py
    response = await async_client.get("/api/cases")
    assert (
        response.status_code == 401
    )  # FastAPI default for missing auth from OAuth2PasswordBearer
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(
    async_client: AsyncClient, test_staff_user: Staff
):
    """Test accessing a protected route with a valid token."""
    # First, log in to get a token
    login_response = await async_client.post(
        "/auth/login", json={"email": TEST_STAFF_EMAIL, "password": TEST_STAFF_PASSWORD}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Now access the protected route
    headers = {"Authorization": f"Bearer {token}"}
    protected_response = await async_client.get("/api/cases", headers=headers)

    # Since it's a stub route, it should return 501 if auth passes
    assert protected_response.status_code == 501
    assert protected_response.json()["detail"] == "Not implemented"

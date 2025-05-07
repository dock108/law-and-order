"""Tests for CORS middleware configuration."""

import pytest
from httpx import AsyncClient

# from sqlalchemy.ext.asyncio import AsyncSession # Needed for test_staff_user - Removed
# Use async_client fixture from conftest.py
# from pi_auto_api.main import app # No longer needed
from pi_auto.db.models import Staff  # Needed for test_staff_user

from .test_auth_login import (  # Relative import & User credentials
    TEST_STAFF_EMAIL,
    TEST_STAFF_PASSWORD,
)

# Assuming conftest provides async_client and db_session/test_staff_user


@pytest.mark.asyncio
async def test_cors_preflight_allowed_origin(async_client: AsyncClient):
    """Test OPTIONS pre-flight request from an allowed origin."""
    origin = "http://localhost:3000"  # Matches default setting
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization, X-Custom-Header",  # Auth
    }
    # Test against a protected route
    response = await async_client.options("/api/cases", headers=headers)

    assert response.status_code == 200, f"Response text: {response.text}"
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "GET" in response.headers.get("access-control-allow-methods", "")
    allowed_headers = response.headers.get("access-control-allow-headers")
    assert allowed_headers is not None
    assert "authorization" in allowed_headers.lower() or "*" in allowed_headers
    assert "x-custom-header" in allowed_headers.lower() or "*" in allowed_headers


@pytest.mark.asyncio
async def test_cors_preflight_disallowed_origin(async_client: AsyncClient):
    """Test OPTIONS pre-flight request from a disallowed origin."""
    origin = "http://evil.com"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
    }
    response = await async_client.options("/api/cases", headers=headers)
    # Check only that the allow-origin header does not match the disallowed origin
    assert response.headers.get("access-control-allow-origin") != origin


@pytest.mark.asyncio
async def test_cors_get_request_allowed_origin(
    async_client: AsyncClient, test_staff_user: Staff
):
    """Test GET request from an allowed origin (authenticated)."""
    # Login first
    login_response = await async_client.post(
        "/auth/login", json={"email": TEST_STAFF_EMAIL, "password": TEST_STAFF_PASSWORD}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    origin = "http://localhost:3000"
    headers = {"Origin": origin, "Authorization": f"Bearer {token}"}
    response = await async_client.get("/api/cases", headers=headers)

    assert response.status_code == 501  # Should succeed auth, hit 501 stub
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_cors_get_request_disallowed_origin(
    async_client: AsyncClient, test_staff_user: Staff
):
    """Test GET request from a disallowed origin (authenticated)."""
    # Login first
    login_response = await async_client.post(
        "/auth/login", json={"email": TEST_STAFF_EMAIL, "password": TEST_STAFF_PASSWORD}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    origin = "http://evil.com"
    headers = {"Origin": origin, "Authorization": f"Bearer {token}"}
    response = await async_client.get("/api/cases", headers=headers)

    assert response.status_code == 501  # Should succeed auth, hit 501 stub
    # Crucially, the allow-origin header should NOT be present or match the bad origin
    assert response.headers.get("access-control-allow-origin") != origin


@pytest.mark.asyncio
async def test_cors_get_request_allowed_origin_no_auth(async_client: AsyncClient):
    """Test GET request from allowed origin without auth fails correctly."""
    origin = "http://localhost:3000"
    headers = {"Origin": origin}
    response = await async_client.get("/api/cases", headers=headers)
    assert response.status_code == 401  # Expect 401 due to missing auth
    # CORS header should still be present even on auth failure for allowed origin
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"

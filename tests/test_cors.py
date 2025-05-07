"""Tests for CORS middleware configuration."""

import pytest
from httpx import AsyncClient

from pi_auto_api.main import app


# Use function scope for client to potentially allow modifying settings per test
@pytest.fixture
async def client() -> AsyncClient:
    """Provides an httpx AsyncClient configured for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_cors_preflight_allowed_origin(client: AsyncClient):
    """Test OPTIONS pre-flight request from an allowed origin."""
    origin = "http://localhost:3000"  # Matches default setting
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Custom-Header",
    }
    response = await client.options("/api/cases", headers=headers)

    assert response.status_code == 200, f"Response text: {response.text}"
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    # Allow any method/header specified in request
    assert "GET" in response.headers.get("access-control-allow-methods", "")
    # Check if requested header is allowed (might be reflected or be '*')
    allowed_headers = response.headers.get("access-control-allow-headers")
    assert allowed_headers is not None
    assert "x-custom-header" in allowed_headers.lower() or "*" in allowed_headers


@pytest.mark.asyncio
async def test_cors_preflight_disallowed_origin(client: AsyncClient):
    """Test OPTIONS pre-flight request from a disallowed origin."""
    origin = "http://evil.com"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
    }
    response = await client.options("/api/cases", headers=headers)

    # A disallowed origin in a simple request *might* still get a 200 on OPTIONS,
    # but it should NOT have the access-control-allow-origin header matching the origin.
    # Some middleware might return 400 or 403, but standard CORS preflight for
    # disallowed origins often results in a 200 OK without allow headers.
    # We primarily care that the allow header isn't present or doesn't match.
    assert response.headers.get("access-control-allow-origin") != origin


@pytest.mark.asyncio
async def test_cors_get_request_allowed_origin(client: AsyncClient):
    """Test GET request from an allowed origin."""
    origin = "http://localhost:3000"
    headers = {"Origin": origin}
    # Note: GET /api/cases is a 501 stub, but CORS headers should still be present
    response = await client.get("/api/cases", headers=headers)

    # Status code depends on the route handler, here it's 501
    assert response.status_code == 501
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_cors_get_request_disallowed_origin(client: AsyncClient):
    """Test GET request from a disallowed origin."""
    origin = "http://evil.com"
    headers = {"Origin": origin}
    response = await client.get("/api/cases", headers=headers)

    # Status code depends on the route handler
    assert response.status_code == 501
    # Crucially, the allow-origin header should NOT be present or match the bad origin
    assert response.headers.get("access-control-allow-origin") != origin

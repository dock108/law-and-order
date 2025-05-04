"""Tests for basic API endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test the root endpoint."""
    response = await async_client.get("/")

    assert response.status_code == status.HTTP_200_OK
    assert "documentation" in response.json()
    assert "health" in response.json()
    assert "readiness" in response.json()
    assert "intake" in response.json()


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Test the health endpoint."""
    response = await async_client.get("/healthz")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_request_id_middleware(async_client: AsyncClient):
    """Test the request ID middleware."""
    # Make a request with a custom request ID
    response = await async_client.get(
        "/healthz", headers={"X-Request-ID": "test-request-id"}
    )

    # Check that the response has the same request ID
    assert response.headers["X-Request-ID"] == "test-request-id"


@pytest.mark.asyncio
async def test_request_id_middleware_generated(async_client: AsyncClient):
    """Test the request ID middleware generates IDs when none provided."""
    # Make a request without a request ID
    response = await async_client.get("/healthz")

    # Check that the response has a generated request ID
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0

"""Tests for health check endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient
from pi_auto_api.main import app, check_database, check_docassemble


async def mock_check_database():
    """Mock database check."""
    return None


async def mock_check_docassemble():
    """Mock Docassemble check."""
    return None


@pytest.mark.asyncio
async def test_readyz_endpoint(async_client: AsyncClient):
    """Test the readiness endpoint with mocked dependencies."""
    # Set up dependency overrides
    original_deps = app.dependency_overrides.copy()
    app.dependency_overrides[check_database] = mock_check_database
    app.dependency_overrides[check_docassemble] = mock_check_docassemble

    try:
        response = await async_client.get("/readyz")

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ok"}
    finally:
        # Clean up overrides
        app.dependency_overrides = original_deps

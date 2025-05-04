"""Tests for edge cases and remaining coverage in main.py."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from pi_auto_api.main import check_database, health_check


@pytest.mark.asyncio
async def test_health_check_function():
    """Test the health_check function directly."""
    result = await health_check()
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_check_database_no_url():
    """Test check_database when SUPABASE_URL is not set."""
    with patch("pi_auto_api.main.settings") as mock_settings:
        mock_settings.SUPABASE_URL = None

        with pytest.raises(HTTPException) as exc_info:
            await check_database()

        assert exc_info.value.status_code == 503
        assert "Database connection pool not available" in exc_info.value.detail


@pytest.mark.asyncio
async def test_check_database_execution_error():
    """Test check_database when SQL execution fails."""
    # Create a mock pool where acquire() itself raises an exception
    mock_pool = AsyncMock()
    # Make acquire() raise an exception directly
    mock_pool.acquire.side_effect = Exception("Connection error")

    with patch("pi_auto_api.main.db_pool", mock_pool):
        with pytest.raises(HTTPException) as exc_info:
            await check_database()

        assert exc_info.value.status_code == 503
        assert "Database not available" in exc_info.value.detail


@pytest.mark.asyncio
async def test_intake_validation_error(async_client: AsyncClient):
    """Test intake endpoint with a validation error from create_intake."""
    # Invalid payload missing required fields
    payload = {
        "client": {},  # Missing required fields
        "incident": {},  # Missing required fields
    }

    # Make the request
    response = await async_client.post("/intake", json=payload)

    # Check status code
    assert response.status_code == 422

    # Pydantic validation errors are returned as a list
    error_detail = response.json()["detail"]
    assert isinstance(error_detail, list)
    assert len(error_detail) > 0

    # Check that at least one validation error exists
    found_validation_error = False
    for error in error_detail:
        if "type" in error and error["type"] in ["missing", "value_error"]:
            found_validation_error = True
            break

    assert found_validation_error, "No validation error found in response"

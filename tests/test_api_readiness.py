"""Tests for the readiness endpoint including error conditions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from httpx import AsyncClient, HTTPError

from pi_auto_api.main import app, check_database, check_docassemble


@pytest.mark.asyncio
async def test_check_database_no_pool():
    """Test check_database when db_pool is None."""
    # Mock settings with valid URL
    with patch("pi_auto_api.main.settings") as mock_settings:
        mock_settings.SUPABASE_URL = "postgresql://user:pass@localhost:5432/db"

        # Mock db_pool as None and asyncpg.create_pool to fail
        with patch("pi_auto_api.main.db_pool", None):
            with patch("pi_auto_api.main.asyncpg.create_pool") as mock_create_pool:
                mock_create_pool.side_effect = Exception("Connection error")

                # Function should raise HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    await check_database()

                assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                assert "Database connection failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_check_database_with_conn_error():
    """Test check_database when connection fails."""
    # Mock pool with failing acquire
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.side_effect = Exception(
        "Connection error"
    )

    with patch("pi_auto_api.main.db_pool", mock_pool):
        # Function should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await check_database()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Database not available" in exc_info.value.detail


@pytest.mark.asyncio
async def test_check_docassemble_connection_error():
    """Test check_docassemble when connection fails."""
    with patch("pi_auto_api.main.settings") as mock_settings:
        mock_settings.DOCASSEMBLE_URL = "http://docassemble:8080"

        # Mock httpx to raise connection error
        with patch("pi_auto_api.main.httpx.AsyncClient") as mock_client:
            client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = client_instance
            client_instance.get.side_effect = HTTPError("Connection failed")

            # Function should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await check_docassemble()

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Docassemble API not available" in exc_info.value.detail


@pytest.mark.asyncio
async def test_check_docassemble_non_200_response():
    """Test check_docassemble when API returns non-200 status."""
    with patch("pi_auto_api.main.settings") as mock_settings:
        mock_settings.DOCASSEMBLE_URL = "http://docassemble:8080"

        # Mock httpx with 500 response
        with patch("pi_auto_api.main.httpx.AsyncClient") as mock_client:
            client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = client_instance

            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            client_instance.get.return_value = mock_response

            # Function should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await check_docassemble()

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Docassemble API not available" in exc_info.value.detail


@pytest.mark.asyncio
async def test_readiness_endpoint_with_db_failure(async_client: AsyncClient):
    """Test the readiness endpoint when database check fails."""

    # Override check_database to raise an exception
    async def failing_check_database():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    # Set up dependency overrides
    original_deps = app.dependency_overrides.copy()
    app.dependency_overrides[check_database] = failing_check_database
    app.dependency_overrides[check_docassemble] = AsyncMock(return_value=None)

    try:
        response = await async_client.get("/readyz")

        # Verify response
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Database not available" in response.json()["detail"]
    finally:
        # Clean up overrides
        app.dependency_overrides = original_deps


@pytest.mark.asyncio
async def test_readiness_endpoint_with_docassemble_failure(async_client: AsyncClient):
    """Test the readiness endpoint when docassemble check fails."""

    # Override check_docassemble to raise an exception
    async def failing_check_docassemble():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docassemble API not available",
        )

    # Set up dependency overrides
    original_deps = app.dependency_overrides.copy()
    app.dependency_overrides[check_database] = AsyncMock(return_value=None)
    app.dependency_overrides[check_docassemble] = failing_check_docassemble

    try:
        response = await async_client.get("/readyz")

        # Verify response
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Docassemble API not available" in response.json()["detail"]
    finally:
        # Clean up overrides
        app.dependency_overrides = original_deps

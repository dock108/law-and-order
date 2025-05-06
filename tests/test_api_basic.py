"""Basic API tests.

This module contains tests for the PI Automation API's basic endpoints.
"""

import os

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from httpx import AsyncClient

from pi_auto_api.main import app, check_database, check_docassemble

# Set test environment variables for settings
os.environ["SUPABASE_URL"] = "postgresql://testuser:testpassword@localhost:5432/testdb"
os.environ["SUPABASE_KEY"] = "test-key"


@pytest_asyncio.fixture
async def async_client():
    """Return an async client for testing API endpoints."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test the health check endpoint."""
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_request_id_middleware(async_client):
    """Test the request ID middleware."""
    response = await async_client.get("/healthz")
    assert "X-Request-ID" in response.headers

    # Test with provided request ID
    test_id = "test-request-id"
    response = await async_client.get("/healthz", headers={"X-Request-ID": test_id})
    assert response.headers["X-Request-ID"] == test_id


@pytest.mark.asyncio
async def test_readyz_success(async_client):
    """Test the readiness check endpoint when everything is available."""

    # Override dependencies with noop functions
    async def mock_check_database():
        return None

    async def mock_check_docassemble():
        return None

    # Use dependency_overrides to inject mocks
    app.dependency_overrides[check_database] = mock_check_database
    app.dependency_overrides[check_docassemble] = mock_check_docassemble

    try:
        response = await async_client.get("/readyz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_readyz_db_failure(async_client):
    """Test the readiness check endpoint when the database is not available."""

    # Override dependencies - database fails, docassemble succeeds
    async def mock_check_database():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available: connection refused",
        )

    async def mock_check_docassemble():
        return None

    # Use dependency_overrides to inject mocks
    app.dependency_overrides[check_database] = mock_check_database
    app.dependency_overrides[check_docassemble] = mock_check_docassemble

    try:
        response = await async_client.get("/readyz")
        assert response.status_code == 503
        assert "Database not available" in response.json()["detail"]
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_readyz_docassemble_failure(async_client):
    """Test the readiness check endpoint when Docassemble is not available."""

    # Override dependencies - database succeeds, docassemble fails
    async def mock_check_database():
        return None

    async def mock_check_docassemble():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docassemble API not available: Internal Server Error",
        )

    # Use dependency_overrides to inject mocks
    app.dependency_overrides[check_database] = mock_check_database
    app.dependency_overrides[check_docassemble] = mock_check_docassemble

    try:
        response = await async_client.get("/readyz")
        assert response.status_code == 503
        assert "Docassemble API not available" in response.json()["detail"]
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_readyz_both_failing(async_client):
    """Test readiness check when both database and Docassemble fail."""

    # Override dependencies - both fail (database error takes precedence)
    async def mock_check_database():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available: connection refused",
        )

    async def mock_check_docassemble():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docassemble API not available: Connection refused",
        )

    # Use dependency_overrides to inject mocks
    app.dependency_overrides[check_database] = mock_check_database
    app.dependency_overrides[check_docassemble] = mock_check_docassemble

    try:
        response = await async_client.get("/readyz")
        assert response.status_code == 503
        assert "Database not available" in response.json()["detail"]
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    """Test the root endpoint returns correct JSON."""
    response = await async_client.get("/")
    assert response.status_code == 200

    # Check all expected keys are present
    data = response.json()
    assert "message" in data
    assert "documentation" in data
    assert "health" in data
    assert "readiness" in data

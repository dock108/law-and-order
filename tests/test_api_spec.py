"""Tests for the API specification and stub routes."""

from pathlib import Path

import pytest
import yaml
from httpx import AsyncClient
from openapi_spec_validator import validate

from pi_auto.db.models import Staff

from .test_auth_login import TEST_STAFF_EMAIL, TEST_STAFF_PASSWORD

# Define the routes to test (path only)
STUB_ROUTES = [
    ("GET", "/api/cases"),
    ("GET", "/api/cases/testcaseid"),
    ("POST", "/api/cases/testcaseid/advance"),
    ("GET", "/api/tasks"),
    ("POST", "/api/tasks"),
    ("PATCH", "/api/tasks/testtaskid"),
    ("DELETE", "/api/tasks/testtaskid"),
    ("POST", "/api/tasks/bulk-complete"),
    ("GET", "/api/documents"),
    ("POST", "/api/documents/testdocid/send"),
]

# SSE route - may or may not need auth
SSE_ROUTE = ("GET", "/api/events/stream")


@pytest.mark.asyncio
@pytest.mark.parametrize("method, path", STUB_ROUTES)
async def test_stub_routes_require_auth(
    async_client: AsyncClient, method: str, path: str
):
    """Test that stub routes return 401 without authentication."""
    response = await async_client.request(method, path)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
@pytest.mark.parametrize("method, path", STUB_ROUTES)
async def test_stub_routes_return_501_with_auth(
    async_client: AsyncClient, test_staff_user: Staff, method: str, path: str
):
    """Test that stub routes return 501 when authenticated."""
    # Log in the test user
    login_response = await async_client.post(
        "/auth/login", json={"email": TEST_STAFF_EMAIL, "password": TEST_STAFF_PASSWORD}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Make request to the stub route with auth header
    response = await async_client.request(method, path, headers=headers)
    assert response.status_code == 501
    assert response.json() == {"detail": "Not implemented"}


def test_openapi_spec_is_valid():
    """Test that the openapi/pi-workflow.yaml spec is valid OpenAPI."""
    spec_path = Path("openapi/pi-workflow.yaml")
    assert spec_path.exists(), f"OpenAPI spec file not found at {spec_path}"

    with open(spec_path, "r") as f:
        spec_content = yaml.safe_load(f)

    # Validate the spec content
    validate(spec_content)

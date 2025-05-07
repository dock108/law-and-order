"""Tests for the API specification and stub routes."""

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from openapi_spec_validator import validate

from pi_auto_api.main import app

client = TestClient(app)

# Define the routes and their expected non-SSE status codes
STUB_ROUTES_NON_SSE = [
    ("GET", "/api/cases", 501),
    ("GET", "/api/cases/testcaseid", 501),
    ("POST", "/api/cases/testcaseid/advance", 501),
    ("GET", "/api/tasks", 501),
    ("POST", "/api/tasks", 501),
    ("PATCH", "/api/tasks/testtaskid", 501),
    ("DELETE", "/api/tasks/testtaskid", 501),
    ("POST", "/api/tasks/bulk-complete", 501),
    ("GET", "/api/documents", 501),
    ("POST", "/api/documents/testdocid/send", 501),
]

# SSE route
SSE_ROUTE = ("GET", "/api/events/stream", 501)


@pytest.mark.parametrize("method, path, expected_status", STUB_ROUTES_NON_SSE)
def test_stub_routes_return_501(method: str, path: str, expected_status: int):
    """Test that non-SSE stub routes return 501 Not Implemented."""
    response = client.request(method, path)
    assert response.status_code == expected_status
    if response.status_code == 501:  # Should always be true for these tests
        assert response.json() == {"detail": "Not implemented"}


def test_sse_event_stream_returns_501():
    """Test that the SSE event stream stub route returns 501 Not Implemented."""
    method, path, expected_status = SSE_ROUTE
    response = client.request(method, path)
    assert response.status_code == expected_status
    if response.status_code == 501:  # Should always be true for this test
        assert response.text == ""


def test_openapi_spec_is_valid():
    """Test that the openapi/pi-workflow.yaml spec is valid OpenAPI."""
    spec_path = Path("openapi/pi-workflow.yaml")
    assert spec_path.exists(), f"OpenAPI spec file not found at {spec_path}"

    with open(spec_path, "r") as f:
        spec_content = yaml.safe_load(f)

    # Validate the spec content
    # The validate function from openapi_spec_validator is used here.
    validate(spec_content)

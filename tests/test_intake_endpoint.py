"""Tests for the intake endpoint."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from pi_auto_api.schemas import IntakePayload

# Sample valid payload
VALID_PAYLOAD = {
    "client": {
        "full_name": "John Doe",
        "dob": "1980-01-01",
        "phone": "555-123-4567",
        "email": "john.doe@example.com",
        "address": "123 Main St, Anytown, USA 12345",
    },
    "incident": {
        "date": "2023-05-15",
        "location": "Intersection of 1st Ave and Main St",
        "police_report_url": "https://example.com/police-report-123",
        "injuries": ["Whiplash", "Back pain"],
        "vehicle_damage_text": "Front bumper damage and broken headlight",
    },
}

# Sample invalid payload (missing email)
INVALID_PAYLOAD = {
    "client": {
        "full_name": "John Doe",
        "dob": "1980-01-01",
        "phone": "555-123-4567",
        "address": "123 Main St, Anytown, USA 12345",
        # missing email
    },
    "incident": {
        "date": "2023-05-15",
        "location": "Intersection of 1st Ave and Main St",
    },
}


@pytest.fixture
def mock_create_intake():
    """Mock the create_intake function."""
    with patch("pi_auto_api.main.create_intake") as mock:
        # Set up the mock to return the result directly
        mock.return_value = {"client_id": 123, "incident_id": 456}
        yield mock


@pytest.fixture
def mock_generate_retainer():
    """Mock the generate_retainer task."""
    with patch("pi_auto_api.main.generate_retainer") as mock:
        # Create mock for .delay() method
        mock.delay = AsyncMock()
        yield mock


@pytest.mark.asyncio
async def test_intake_success(
    mock_create_intake, mock_generate_retainer, async_client: AsyncClient
):
    """Test successful intake creation."""
    response = await async_client.post(
        "/intake",
        json=VALID_PAYLOAD,
    )

    # Assert response status and content
    assert response.status_code == status.HTTP_202_ACCEPTED
    response_json = response.json()
    assert response_json["client_id"] == 123
    assert response_json["incident_id"] == 456
    assert response_json["status"] == "processing"

    # Assert create_intake was called with correct data
    mock_create_intake.assert_called_once()
    call_arg = mock_create_intake.call_args[0][0]
    assert isinstance(call_arg, IntakePayload)
    assert call_arg.client.full_name == "John Doe"
    assert call_arg.incident.date == date(2023, 5, 15)

    # Assert Celery task was queued
    mock_generate_retainer.delay.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_intake_validation_error(async_client: AsyncClient):
    """Test intake with invalid payload."""
    response = await async_client.post(
        "/intake",
        json=INVALID_PAYLOAD,
    )

    # Assert response status
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_intake_database_error(mock_create_intake, async_client: AsyncClient):
    """Test intake with database error."""
    # Configure mock to raise an exception
    mock_create_intake.side_effect = Exception("Database error")

    response = await async_client.post(
        "/intake",
        json=VALID_PAYLOAD,
    )

    # Assert response status
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to create intake" in response.json()["detail"]

"""Tests for the full generate_retainer Celery task."""

from unittest.mock import AsyncMock, patch

import pytest

# Import the async helper function directly for testing
from pi_auto_api.tasks.retainer import _run_retainer_flow

# Dummy PDF content for mocking
DUMMY_PDF_BYTES = b"%PDF-1.7..."
DUMMY_ENVELOPE_ID = "fake-envelope-id-12345"
CLIENT_ID = 99


@pytest.fixture
def mock_db_payload():
    """Provides a sample payload similar to what get_client_payload returns."""
    return {
        "client": {
            "full_name": "Test Client",
            "dob": "1990-01-01",
            "phone": "555-555-5555",
            "email": "test.client@example.com",
            "address": "123 Test St",
        },
        "incident": {
            "date": "2024-01-01",
            "location": "Test Location",
            "injuries": ["Testing"],
            "vehicle_damage_text": "Test Damage",
        },
    }


@pytest.mark.integration
@pytest.mark.asyncio  # Mark test as async
async def test_generate_retainer_success(mock_db_payload):
    """Test the _run_retainer_flow helper successfully completes the flow.

    Mocks database and external API calls.
    """
    # Patch the helper functions used within _run_retainer_flow
    with (
        patch(
            "pi_auto_api.tasks.retainer.get_client_payload", new_callable=AsyncMock
        ) as mock_get_payload,
        patch(
            "pi_auto_api.tasks.retainer.generate_retainer_pdf", new_callable=AsyncMock
        ) as mock_gen_pdf,
        patch(
            "pi_auto_api.tasks.retainer.send_envelope", new_callable=AsyncMock
        ) as mock_send_env,
    ):
        # Configure mock return values
        mock_get_payload.return_value = mock_db_payload
        mock_gen_pdf.return_value = DUMMY_PDF_BYTES
        mock_send_env.return_value = DUMMY_ENVELOPE_ID

        # Execute the async helper function directly
        result = await _run_retainer_flow(CLIENT_ID)

        # Assertions
        mock_get_payload.assert_called_once_with(CLIENT_ID)
        mock_gen_pdf.assert_called_once_with(mock_db_payload)
        mock_send_env.assert_called_once_with(
            DUMMY_PDF_BYTES,
            mock_db_payload["client"]["email"],
            mock_db_payload["client"]["full_name"],
        )

        assert result == {
            "client_id": CLIENT_ID,
            "envelope_id": DUMMY_ENVELOPE_ID,
            "status": "completed",
        }

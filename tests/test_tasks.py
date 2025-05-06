"""Tests for the task helper functions."""

from unittest.mock import AsyncMock, patch

import pytest

from pi_auto_api.tasks.retainer import _run_retainer_flow


@pytest.mark.asyncio
async def test_run_retainer_flow_success():
    """Test the _run_retainer_flow helper directly with mocks."""
    client_id = 123
    expected_payload = {
        "client": {"email": "test@example.com", "full_name": "Test Client"}
    }
    expected_pdf = b"pdf-content"
    expected_envelope = "env-12345"

    # Patch dependencies within the test scope
    with (
        patch(
            "pi_auto_api.tasks.retainer.get_client_payload", new_callable=AsyncMock
        ) as mock_payload,
        patch(
            "pi_auto_api.tasks.retainer.generate_retainer_pdf", new_callable=AsyncMock
        ) as mock_pdf,
        patch(
            "pi_auto_api.tasks.retainer.send_envelope", new_callable=AsyncMock
        ) as mock_envelope,
    ):
        # Set mock return values
        mock_payload.return_value = expected_payload
        mock_pdf.return_value = expected_pdf
        mock_envelope.return_value = expected_envelope

        # Call the async helper directly
        result = await _run_retainer_flow(client_id)

        # Verify calls and result
        mock_payload.assert_awaited_once_with(client_id)
        mock_pdf.assert_awaited_once_with(expected_payload)
        mock_envelope.assert_awaited_once_with(
            expected_pdf,
            expected_payload["client"]["email"],
            expected_payload["client"]["full_name"],
        )
        assert result == {
            "client_id": client_id,
            "envelope_id": expected_envelope,
            "status": "completed",
        }


# Add your tests here

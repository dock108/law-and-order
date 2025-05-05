"""Tests for insurance notice functionality."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pi_auto_api.main import app


@pytest.fixture
def test_client():
    """Return a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def docusign_webhook_payload():
    """Return a test DocuSign webhook payload."""
    return {
        "envelopeId": "12345-6789-abcdef",
        "status": "completed",
        "emailSubject": "Retainer Agreement ID: 101",
        "customFields": [{"name": "client_id", "value": "101"}],
    }


@pytest.fixture
def mock_send_insurance_notice():
    """Mock the send_insurance_notice Celery task."""
    with patch("pi_auto_api.main.send_insurance_notice") as mock_task:
        mock_task.delay = MagicMock()
        yield mock_task


def test_docusign_webhook_success(
    test_client, docusign_webhook_payload, mock_send_insurance_notice
):
    """Test successful processing of a DocuSign webhook."""
    response = test_client.post("/webhooks/docusign", json=docusign_webhook_payload)

    # Check response
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["client_id"] == "101"

    # Verify task was queued
    mock_send_insurance_notice.delay.assert_called_once_with(101)


def test_docusign_webhook_non_completed(
    test_client, docusign_webhook_payload, mock_send_insurance_notice
):
    """Test handling of non-completed envelope status."""
    # Modify payload to have non-completed status
    docusign_webhook_payload["status"] = "sent"

    response = test_client.post("/webhooks/docusign", json=docusign_webhook_payload)

    # Check response
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["reason"] == "not_completed"

    # Verify task was not queued
    mock_send_insurance_notice.delay.assert_not_called()


def test_docusign_webhook_parsing_error(
    test_client, docusign_webhook_payload, mock_send_insurance_notice
):
    """Test handling of payload parsing errors."""
    # Remove required field
    del docusign_webhook_payload["envelopeId"]

    response = test_client.post("/webhooks/docusign", json=docusign_webhook_payload)

    # Check response code (should be validation error)
    assert response.status_code == 422

    # Verify task was not queued
    mock_send_insurance_notice.delay.assert_not_called()


@pytest.mark.asyncio
@patch("pi_auto_api.tasks.insurance_notice.get_insurance_payload")
@patch("pi_auto_api.tasks.insurance_notice.generate_letter")
@patch("pi_auto_api.tasks.insurance_notice.send_fax")
async def test_insurance_notice_task(
    mock_send_fax, mock_generate_letter, mock_get_payload
):
    """Test the insurance notice Celery task."""
    from pi_auto_api.tasks.insurance_notice import _run_insurance_notice_flow

    # Mock the database response
    mock_get_payload.return_value = {
        "client": {
            "full_name": "Test Client",
            "email": "client@example.com",
        },
        "incident": {"date": "2023-01-01", "location": "Test Location"},
        "client_insurance": {
            "carrier_name": "Test Client Insurance",
            "policy_number": "CL123456",
        },
        "adverse_insurance": [
            {
                "carrier_name": "Test Adverse Insurance",
                "policy_number": "ADV789012",
            }
        ],
    }

    # Mock the letter generation
    mock_generate_letter.return_value = b"PDF bytes"

    # Mock the fax sending
    mock_send_fax.return_value = "FX12345"

    # Run the task
    result = await _run_insurance_notice_flow(101)

    # Verify results
    assert result["client_id"] == 101
    assert len(result["faxes_sent"]) == 2  # One for client insurance, one for adverse
    assert any(
        item["carrier"] == "Test Client Insurance" for item in result["faxes_sent"]
    )
    assert any(
        item["carrier"] == "Test Adverse Insurance" for item in result["faxes_sent"]
    )

    # Verify mocks were called correctly
    mock_get_payload.assert_called_once_with(101)
    mock_generate_letter.assert_called_once()
    assert mock_send_fax.call_count == 2

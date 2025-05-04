"""Tests for the DocuSign client utility."""

import asyncio  # Import asyncio
import base64
from unittest.mock import MagicMock, mock_open, patch  # Remove AsyncMock

import pytest
from docusign_esign import (
    ApiClient,
    ApiException,
    Document,
    EnvelopeDefinition,
    EnvelopesApi,
    Recipients,
    Signer,
    SignHere,
    Tabs,
)
from fastapi import HTTPException
from pi_auto_api.externals.docusign import (
    _get_docusign_api_client,
    send_envelope,
)

# Mock settings values
FAKE_SETTINGS = {
    "DOCUSIGN_BASE_URL": "https://fake.docusign.net/restapi",
    "DOCUSIGN_ACCOUNT_ID": "fake-account-id",
    "DOCUSIGN_INTEGRATOR_KEY": "fake-int-key",
    "DOCUSIGN_USER_ID": "fake-user-id",
    "DOCUSIGN_PRIVATE_KEY": "fake_private.key",
}

FAKE_PDF_BYTES = b"%PDF..."
CLIENT_EMAIL = "signer@example.com"
CLIENT_NAME = "Signer Name"
EXPECTED_ENVELOPE_ID = "test-envelope-123"


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the DocuSign API client cache before each test."""
    # Import the module variables directly for resetting
    from pi_auto_api.externals.docusign import _api_client_cache, _token_expiry

    # Save original values
    old_cache = _api_client_cache
    old_expiry = _token_expiry

    # Reset cache
    import pi_auto_api.externals.docusign

    pi_auto_api.externals.docusign._api_client_cache = None
    pi_auto_api.externals.docusign._token_expiry = None

    yield

    # Restore original values after test
    pi_auto_api.externals.docusign._api_client_cache = old_cache
    pi_auto_api.externals.docusign._token_expiry = old_expiry


@patch("pi_auto_api.externals.docusign.settings", MagicMock(**FAKE_SETTINGS))
@patch("pi_auto_api.externals.docusign.ApiClient")
@patch("builtins.open", new_callable=mock_open, read_data="fake-key-content")
def test_get_docusign_api_client_success(mock_file_open, MockApiClient):
    """Test successful DocuSign ApiClient configuration with JWT."""
    mock_api_instance = MagicMock()
    MockApiClient.return_value = mock_api_instance

    api_client = _get_docusign_api_client()

    MockApiClient.assert_called_once()
    assert api_client.host == FAKE_SETTINGS["DOCUSIGN_BASE_URL"]
    mock_file_open.assert_called_once_with(FAKE_SETTINGS["DOCUSIGN_PRIVATE_KEY"], "r")
    mock_api_instance.configure_jwt_authorization_flow.assert_called_once_with(
        private_key="fake-key-content",
        client_id=FAKE_SETTINGS["DOCUSIGN_INTEGRATOR_KEY"],
        user_id=FAKE_SETTINGS["DOCUSIGN_USER_ID"],
        scopes=["signature", "impersonation"],
        expires_in=3600,
    )
    assert api_client == mock_api_instance


@patch("pi_auto_api.externals.docusign.settings", MagicMock(**FAKE_SETTINGS))
@patch("pi_auto_api.externals.docusign.logger")  # Add logger mock
def test_get_docusign_api_client_key_not_found(mock_logger):
    """Test FileNotFoundError when private key is missing."""
    with patch(
        "pi_auto_api.externals.docusign._read_private_key",
        side_effect=FileNotFoundError("DocuSign private key not found at: fake_path"),
    ):
        with pytest.raises(FileNotFoundError, match="DocuSign private key not found"):
            _get_docusign_api_client()

    # Verify warning was logged
    mock_logger.warning.assert_called_once()


@patch("pi_auto_api.externals.docusign.settings", MagicMock(**FAKE_SETTINGS))
@patch("builtins.open", new_callable=mock_open, read_data="fake-key-content")
@patch("pi_auto_api.externals.docusign.ApiClient")
def test_get_docusign_api_client_jwt_error(MockApiClient, mock_file_open):
    """Test HTTPException is raised on JWT authentication failure."""
    mock_api_instance = MagicMock()
    api_exception = ApiException(status=500, reason="JWT Error")
    mock_api_instance.configure_jwt_authorization_flow.side_effect = api_exception
    MockApiClient.return_value = mock_api_instance

    with pytest.raises(HTTPException) as exc_info:
        _get_docusign_api_client()

    assert exc_info.value.status_code == 500
    assert "DocuSign authentication error" in exc_info.value.detail


@pytest.mark.asyncio
@patch("pi_auto_api.externals.docusign.settings", MagicMock(**FAKE_SETTINGS))
@patch("pi_auto_api.externals.docusign._get_docusign_api_client")
@patch("pi_auto_api.externals.docusign.EnvelopesApi")
async def test_send_envelope_success(MockEnvelopesApi, mock_get_api_client):
    """Test successful envelope creation and sending."""
    # Mock the API client and EnvelopesApi
    mock_api_client_instance = MagicMock(spec=ApiClient)
    mock_api_client_instance.loop = (
        asyncio.get_running_loop()
    )  # Mock loop for run_in_executor
    mock_get_api_client.return_value = mock_api_client_instance

    mock_envelopes_api_instance = MagicMock(spec=EnvelopesApi)
    mock_create_env_result = MagicMock(envelope_id=EXPECTED_ENVELOPE_ID)
    # Mock the synchronous create_envelope call inside run_in_executor
    mock_envelopes_api_instance.create_envelope.return_value = mock_create_env_result
    MockEnvelopesApi.return_value = mock_envelopes_api_instance

    # Call the function
    envelope_id = await send_envelope(FAKE_PDF_BYTES, CLIENT_EMAIL, CLIENT_NAME)

    # Assertions
    mock_get_api_client.assert_called_once()
    MockEnvelopesApi.assert_called_once_with(mock_api_client_instance)

    # Check that create_envelope was called (via run_in_executor)
    assert mock_envelopes_api_instance.create_envelope.call_count == 1
    call_args = mock_envelopes_api_instance.create_envelope.call_args
    assert call_args[1]["account_id"] == FAKE_SETTINGS["DOCUSIGN_ACCOUNT_ID"]

    # Check envelope definition details
    env_def = call_args[1]["envelope_definition"]
    assert isinstance(env_def, EnvelopeDefinition)
    assert env_def.email_subject == "Please Sign: Retainer Agreement"
    assert env_def.status == "sent"
    assert len(env_def.documents) == 1
    doc = env_def.documents[0]
    assert isinstance(doc, Document)
    assert doc.document_id == "1"
    assert doc.name == "Retainer Agreement"
    assert doc.file_extension == "pdf"
    assert base64.b64decode(doc.document_base64) == FAKE_PDF_BYTES

    assert isinstance(env_def.recipients, Recipients)
    assert len(env_def.recipients.signers) == 1
    signer = env_def.recipients.signers[0]
    assert isinstance(signer, Signer)
    assert signer.email == CLIENT_EMAIL
    assert signer.name == CLIENT_NAME
    assert signer.recipient_id == "1"
    # Basic check for tabs
    assert isinstance(signer.tabs, Tabs)
    assert len(signer.tabs.sign_here_tabs) == 1
    assert isinstance(signer.tabs.sign_here_tabs[0], SignHere)

    assert envelope_id == EXPECTED_ENVELOPE_ID


@pytest.mark.asyncio
@patch("pi_auto_api.externals.docusign.settings", MagicMock(**FAKE_SETTINGS))
@patch("pi_auto_api.externals.docusign._get_docusign_api_client")
@patch("pi_auto_api.externals.docusign.EnvelopesApi")
async def test_send_envelope_api_error(MockEnvelopesApi, mock_get_api_client):
    """Test handling of ApiException during envelope creation."""
    mock_api_client_instance = MagicMock(spec=ApiClient)
    mock_api_client_instance.loop = asyncio.get_running_loop()
    mock_get_api_client.return_value = mock_api_client_instance

    mock_envelopes_api_instance = MagicMock(spec=EnvelopesApi)
    # Simulate ApiException from the sync call within run_in_executor
    api_exception = ApiException(
        status=400,
        reason="Bad Request",
        http_resp=MagicMock(data=b'{"errorCode": "INVALID_REQUEST"}'),
    )
    mock_envelopes_api_instance.create_envelope.side_effect = api_exception
    MockEnvelopesApi.return_value = mock_envelopes_api_instance

    with pytest.raises(HTTPException) as exc_info:
        await send_envelope(FAKE_PDF_BYTES, CLIENT_EMAIL, CLIENT_NAME)

    assert exc_info.value.status_code == 500  # We map internal errors to 500
    assert "DocuSign API error" in exc_info.value.detail

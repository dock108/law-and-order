"""Tests for Twilio client functionality."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from pi_auto_api.externals.twilio_client import send_fax, send_sms
from twilio.base.exceptions import TwilioRestException

# Test constants
TEST_PHONE = "+15551234567"
TEST_MESSAGE = "This is a test SMS message"
TEST_MEDIA_URL = "https://example.com/document.pdf"
TEST_SMS_SID = "SM123456789abcdef"
TEST_FAX_SID = "FX123456789abcdef"


@pytest.fixture
def mock_twilio_client():
    """Mock the Twilio client for testing."""
    with patch("pi_auto_api.externals.twilio_client.Client") as mock_client:
        # Create mock response objects
        mock_message = MagicMock()
        mock_message.sid = TEST_SMS_SID

        mock_fax = MagicMock()
        mock_fax.sid = TEST_FAX_SID

        # Set up the mock client structure
        client_instance = mock_client.return_value
        client_instance.messages.create.return_value = mock_message

        # For fax, we need to mock the nested structure
        mock_faxes = MagicMock()
        mock_faxes.create.return_value = mock_fax
        mock_fax_v1 = MagicMock()
        mock_fax_v1.faxes = mock_faxes
        client_instance.fax.v1 = mock_fax_v1

        yield client_instance


@pytest.fixture
def mock_twilio_settings():
    """Mock Twilio settings."""
    with patch("pi_auto_api.externals.twilio_client.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "test_account_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_auth_token"
        mock_settings.TWILIO_SMS_FROM = "+15557654321"
        mock_settings.TWILIO_FAX_FROM = "+15557654321"
        yield mock_settings


@pytest.mark.asyncio
async def test_send_sms_success(mock_twilio_client, mock_twilio_settings):
    """Test successful SMS sending."""
    result = await send_sms(to=TEST_PHONE, body=TEST_MESSAGE)

    # Verify the result
    assert result == TEST_SMS_SID

    # Verify the client was called with correct parameters
    mock_twilio_client.messages.create.assert_called_once_with(
        body=TEST_MESSAGE, from_=mock_twilio_settings.TWILIO_SMS_FROM, to=TEST_PHONE
    )


@pytest.mark.asyncio
async def test_send_fax_success(mock_twilio_client, mock_twilio_settings):
    """Test successful fax sending."""
    result = await send_fax(to=TEST_PHONE, media_url=TEST_MEDIA_URL)

    # Verify the result
    assert result == TEST_FAX_SID

    # Verify the client was called with correct parameters
    mock_twilio_client.fax.v1.faxes.create.assert_called_once_with(
        from_=mock_twilio_settings.TWILIO_FAX_FROM,
        to=TEST_PHONE,
        media_url=TEST_MEDIA_URL,
    )


@pytest.mark.asyncio
async def test_send_sms_with_custom_from(mock_twilio_client, mock_twilio_settings):
    """Test SMS sending with custom from number."""
    custom_from = "+15559876543"
    result = await send_sms(to=TEST_PHONE, body=TEST_MESSAGE, from_number=custom_from)

    # Verify the result
    assert result == TEST_SMS_SID

    # Verify the client was called with correct parameters
    mock_twilio_client.messages.create.assert_called_once_with(
        body=TEST_MESSAGE, from_=custom_from, to=TEST_PHONE
    )


@pytest.mark.asyncio
async def test_send_sms_retry_success(mock_twilio_client, mock_twilio_settings):
    """Test SMS retry logic with eventual success."""
    # Mock first call to fail with a 500 error, then succeed
    error_response = TwilioRestException(
        status=500, uri="test_uri", msg="Server error", method="POST", details={}
    )

    # Configure the mock to fail once then succeed
    mock_twilio_client.messages.create.side_effect = [
        error_response,
        mock_twilio_client.messages.create.return_value,
    ]

    # Patch sleep to avoid waiting in tests
    with patch("time.sleep") as mock_sleep:
        result = await send_sms(to=TEST_PHONE, body=TEST_MESSAGE)

    # Verify the result
    assert result == TEST_SMS_SID

    # Verify the client was called twice
    assert mock_twilio_client.messages.create.call_count == 2

    # Verify sleep was called once with backoff time
    mock_sleep.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_send_fax_retry_success(mock_twilio_client, mock_twilio_settings):
    """Test fax retry logic with eventual success."""
    # Mock first call to fail with a 429 error, then succeed
    error_response = TwilioRestException(
        status=429, uri="test_uri", msg="Too Many Requests", method="POST", details={}
    )

    # Configure the mock to fail once then succeed
    mock_twilio_client.fax.v1.faxes.create.side_effect = [
        error_response,
        mock_twilio_client.fax.v1.faxes.create.return_value,
    ]

    # Patch sleep to avoid waiting in tests
    with patch("time.sleep") as mock_sleep:
        result = await send_fax(to=TEST_PHONE, media_url=TEST_MEDIA_URL)

    # Verify the result
    assert result == TEST_FAX_SID

    # Verify the client was called twice
    assert mock_twilio_client.fax.v1.faxes.create.call_count == 2

    # Verify sleep was called once with backoff time
    mock_sleep.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_send_sms_max_retries_exceeded(mock_twilio_client, mock_twilio_settings):
    """Test SMS retry logic when max retries is exceeded."""
    # Mock a 500 error for all attempts
    error_response = TwilioRestException(
        status=500, uri="test_uri", msg="Server error", method="POST", details={}
    )

    # Configure the mock to always fail
    mock_twilio_client.messages.create.side_effect = error_response

    # Patch sleep to avoid waiting in tests
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(HTTPException) as exc_info:
            await send_sms(to=TEST_PHONE, body=TEST_MESSAGE, max_attempts=3)

    # Verify exception details
    assert exc_info.value.status_code == 500
    assert "Failed to send SMS" in exc_info.value.detail

    # Verify the client was called 3 times (initial + 2 retries)
    assert mock_twilio_client.messages.create.call_count == 3

    # Verify sleep was called twice with increasing backoff times
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1)  # First retry
    mock_sleep.assert_any_call(2)  # Second retry with doubled backoff


@pytest.mark.asyncio
async def test_send_fax_non_retryable_error(mock_twilio_client, mock_twilio_settings):
    """Test fax sending with a non-retryable error (4xx)."""
    # Mock a 400 error (not retryable)
    error_response = TwilioRestException(
        status=400, uri="test_uri", msg="Bad Request", method="POST", details={}
    )

    # Configure the mock to fail
    mock_twilio_client.fax.v1.faxes.create.side_effect = error_response

    # Patch sleep to verify it's not called
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(HTTPException) as exc_info:
            await send_fax(to=TEST_PHONE, media_url=TEST_MEDIA_URL)

    # Verify exception details
    assert exc_info.value.status_code == 500
    assert "Failed to send fax" in exc_info.value.detail

    # Verify the client was called only once (no retries for 4xx)
    assert mock_twilio_client.fax.v1.faxes.create.call_count == 1

    # Verify sleep was not called
    mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_missing_twilio_credentials():
    """Test error when Twilio credentials are not configured."""
    with patch("pi_auto_api.externals.twilio_client.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = None
        mock_settings.TWILIO_AUTH_TOKEN = None

        with pytest.raises(ValueError, match="Twilio credentials not configured"):
            await send_sms(to=TEST_PHONE, body=TEST_MESSAGE)


@pytest.mark.asyncio
async def test_missing_twilio_sms_from():
    """Test error when TWILIO_SMS_FROM is not configured."""
    with patch("pi_auto_api.externals.twilio_client.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "test_account_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_auth_token"
        mock_settings.TWILIO_SMS_FROM = None

        with pytest.raises(ValueError, match="Twilio SMS sender number not configured"):
            await send_sms(to=TEST_PHONE, body=TEST_MESSAGE)


@pytest.mark.asyncio
async def test_missing_twilio_fax_from():
    """Test error when TWILIO_FAX_FROM is not configured."""
    with patch("pi_auto_api.externals.twilio_client.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "test_account_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_auth_token"
        mock_settings.TWILIO_FAX_FROM = None

        with pytest.raises(ValueError, match="Twilio fax sender number not configured"):
            await send_fax(to=TEST_PHONE, media_url=TEST_MEDIA_URL)

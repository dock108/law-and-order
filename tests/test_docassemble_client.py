"""Tests for the Docassemble client utility."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from pi_auto_api.externals.docassemble import generate_retainer_pdf

SAMPLE_PAYLOAD = {"client": {"name": "Test"}}
DUMMY_PDF_BYTES = b"%PDF-1.7..."
DOCASSEMBLE_API_URL = "http://fake-da.com/api/v1/generate/retainer"


@pytest.mark.asyncio
@patch("pi_auto_api.externals.docassemble.settings")
@patch("pi_auto_api.externals.docassemble.httpx.AsyncClient")
async def test_generate_retainer_pdf_success(MockAsyncClient, mock_settings):
    """Test successful PDF generation via Docassemble API."""
    mock_settings.DOCASSEMBLE_URL = "http://fake-da.com"

    # Mock the response object
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = DUMMY_PDF_BYTES
    mock_response.raise_for_status = MagicMock()

    # Mock the client instance and its methods, removing spec=httpx.AsyncClient
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__.return_value = mock_client_instance
    MockAsyncClient.return_value = mock_client_instance

    # Call the function
    pdf_bytes = await generate_retainer_pdf(SAMPLE_PAYLOAD)

    # Assertions
    MockAsyncClient.assert_called_once()
    mock_client_instance.post.assert_awaited_once_with(
        DOCASSEMBLE_API_URL,
        json=SAMPLE_PAYLOAD,
        headers={"Content-Type": "application/json"},
        timeout=60.0,
    )
    mock_response.raise_for_status.assert_called_once()
    assert pdf_bytes == DUMMY_PDF_BYTES


@pytest.mark.asyncio
@patch("pi_auto_api.externals.docassemble.settings")
@patch("pi_auto_api.externals.docassemble.httpx.AsyncClient")
async def test_generate_retainer_pdf_request_error(MockAsyncClient, mock_settings):
    """Test handling of httpx.RequestError during API call."""
    mock_settings.DOCASSEMBLE_URL = "http://fake-da.com"

    # Mock the client instance to raise RequestError on post
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(
        side_effect=httpx.RequestError("Connection failed")
    )
    mock_client_instance.__aenter__.return_value = mock_client_instance
    MockAsyncClient.return_value = mock_client_instance

    # Call and assert exception
    with pytest.raises(HTTPException) as exc_info:
        await generate_retainer_pdf(SAMPLE_PAYLOAD)

    assert exc_info.value.status_code == 503
    assert "Error contacting Docassemble API" in exc_info.value.detail


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, expected_http_status",
    [(400, 400), (404, 400), (500, 500), (502, 500)],
)
@patch("pi_auto_api.externals.docassemble.settings")
@patch("pi_auto_api.externals.docassemble.httpx.AsyncClient")
async def test_generate_retainer_pdf_http_status_error(
    MockAsyncClient, mock_settings, status_code, expected_http_status
):
    """Test handling of httpx.HTTPStatusError (4xx and 5xx)."""
    mock_settings.DOCASSEMBLE_URL = "http://fake-da.com"

    # Mock the response object
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.text = f"{status_code} Error Text"
    # Setup the exception to be raised by raise_for_status
    http_error = httpx.HTTPStatusError(
        f"{status_code} Error", request=MagicMock(), response=mock_response
    )
    mock_response.raise_for_status = MagicMock(side_effect=http_error)

    # Mock the client instance
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__.return_value = mock_client_instance
    MockAsyncClient.return_value = mock_client_instance

    # Call and assert exception
    with pytest.raises(HTTPException) as exc_info:
        await generate_retainer_pdf(SAMPLE_PAYLOAD)

    mock_response.raise_for_status.assert_called_once()
    assert exc_info.value.status_code == expected_http_status
    assert f"Docassemble API error ({status_code})" in exc_info.value.detail
    assert f"{status_code} Error Text" in exc_info.value.detail

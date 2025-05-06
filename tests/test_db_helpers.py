"""Tests for database helper functions."""

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest

from pi_auto_api.db import get_client_payload

# Sample data returned by mock fetchrow
SAMPLE_DB_RECORD = {
    "full_name": "Test Client",
    "dob": date(1990, 1, 1),
    "phone": "555-555-5555",
    "email": "test.client@example.com",
    "address": "123 Test St",
    "incident_date": date(2024, 1, 1),
    "incident_location": "Test Location",
    "incident_injuries": json.dumps(["Testing"]),
    "incident_vehicle_damage_text": "Test Damage",
}

# Expected output after shaping
EXPECTED_PAYLOAD = {
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

CLIENT_ID = 99


@pytest.mark.asyncio
@patch("pi_auto_api.db.settings")
@patch("pi_auto_api.db.asyncpg.connect")
async def test_get_client_payload_success(mock_connect, mock_settings):
    """Test get_client_payload successfully fetches and shapes data."""
    # Configure mocks
    mock_settings.SUPABASE_URL = "fake-url"
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    # Simple MagicMock that returns the sample dict when accessed
    # This mock implicitly evaluates to True
    mock_record = MagicMock()
    mock_record.__getitem__.side_effect = SAMPLE_DB_RECORD.__getitem__
    mock_fetchrow = AsyncMock(return_value=mock_record)
    mock_conn.fetchrow = mock_fetchrow
    mock_connect.return_value = mock_conn

    # Call the function
    payload = await get_client_payload(CLIENT_ID)

    # Assertions
    mock_connect.assert_awaited_once_with("fake-url")
    mock_fetchrow.assert_awaited_once()
    mock_conn.close.assert_awaited_once()
    assert payload == EXPECTED_PAYLOAD


@pytest.mark.asyncio
@patch("pi_auto_api.db.settings")
@patch("pi_auto_api.db.asyncpg.connect")
async def test_get_client_payload_not_found(mock_connect, mock_settings):
    """Test get_client_payload raises ValueError when client not found."""
    # Configure mocks
    mock_settings.SUPABASE_URL = "fake-url"
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    mock_fetchrow = AsyncMock(return_value=None)  # Simulate record not found
    mock_conn.fetchrow = mock_fetchrow
    mock_connect.return_value = mock_conn

    # Call and assert exception
    with pytest.raises(ValueError, match=f"Client with ID {CLIENT_ID} not found."):
        await get_client_payload(CLIENT_ID)

    # Assert connection closed even on error
    mock_conn.close.assert_awaited_once()


@pytest.mark.asyncio
@patch("pi_auto_api.db.settings")
async def test_get_client_payload_no_supabase_url(mock_settings):
    """Test get_client_payload raises ValueError if SUPABASE_URL is not set."""
    mock_settings.SUPABASE_URL = None
    with pytest.raises(ValueError, match="SUPABASE_URL is not set"):
        await get_client_payload(CLIENT_ID)

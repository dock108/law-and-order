"""Tests for the database intake operations."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest
import pytest_asyncio

from pi_auto_api.db import create_intake
from pi_auto_api.schemas import IntakePayload

# Sample valid payload (converted directly to schema during tests)
VALID_PAYLOAD = {
    "client": {
        "full_name": "Jane Smith",
        "dob": "1985-06-15",
        "phone": "555-987-6543",
        "email": "jane.smith@example.com",
        "address": "456 Oak St, Sometown, USA 67890",
    },
    "incident": {
        "date": "2023-06-20",
        "location": "Highway 101, Mile Marker 25",
        "police_report_url": "https://example.com/police-report-456",
        "injuries": ["Broken arm", "Concussion"],
        "vehicle_damage_text": "Side collision damage, passenger door dented",
    },
}


@pytest_asyncio.fixture
async def mock_asyncpg_connection():
    """Create a mock AsyncPG connection."""
    # Create mock for connection and its methods
    conn = AsyncMock()
    conn.fetchval = AsyncMock()
    conn.close = AsyncMock()
    conn.transaction = MagicMock()

    # Configure the transaction context manager
    transaction_context = AsyncMock()
    conn.transaction.return_value = transaction_context
    transaction_context.__aenter__ = AsyncMock()
    transaction_context.__aexit__ = AsyncMock()

    # Mock asyncpg.connect to return our mock connection
    with patch("pi_auto_api.db.asyncpg.connect", return_value=conn):
        yield conn


@pytest.mark.asyncio
async def test_create_intake_success(mock_asyncpg_connection):
    """Test successful creation of intake records."""
    # Configure return values for fetchval
    mock_asyncpg_connection.fetchval.side_effect = [123, 456]  # client_id, incident_id

    # Patch settings to return a URL for SUPABASE_URL
    with patch(
        "pi_auto_api.db.settings.SUPABASE_URL",
        "postgresql://test:test@localhost/testdb",
    ):
        # Create IntakePayload from the sample data
        payload = IntakePayload.model_validate(VALID_PAYLOAD)

        # Call the function
        result = await create_intake(payload)

        # Verify the result
        assert result == {"client_id": 123, "incident_id": 456}

        # Verify the connection was established and closed
        assert mock_asyncpg_connection.close.called

        # Verify transaction was used
        assert mock_asyncpg_connection.transaction.called

        # Verify the correct queries were executed
        # Check client query
        client_call = mock_asyncpg_connection.fetchval.call_args_list[0]
        assert "INSERT INTO client" in client_call[0][0]
        assert client_call[0][1] == payload.client.full_name
        assert client_call[0][2] == payload.client.dob
        assert client_call[0][3] == payload.client.phone
        assert client_call[0][4] == payload.client.email
        assert client_call[0][5] == payload.client.address

        # Check incident query
        incident_call = mock_asyncpg_connection.fetchval.call_args_list[1]
        assert "INSERT INTO incident" in incident_call[0][0]
        assert incident_call[0][1] == 123  # client_id
        assert incident_call[0][2] == payload.incident.date
        assert incident_call[0][3] == payload.incident.location
        assert incident_call[0][4] == str(payload.incident.police_report_url)
        assert json.loads(incident_call[0][5]) == payload.incident.injuries
        assert incident_call[0][6] == payload.incident.vehicle_damage_text


@pytest.mark.asyncio
async def test_create_intake_missing_settings():
    """Test create_intake with missing SUPABASE_URL."""
    # Patch settings to return None for SUPABASE_URL
    with patch("pi_auto_api.db.settings.SUPABASE_URL", None):
        payload = IntakePayload.model_validate(VALID_PAYLOAD)

        # Verify ValueError is raised
        with pytest.raises(ValueError, match="SUPABASE_URL is not set"):
            await create_intake(payload)


@pytest.mark.asyncio
async def test_create_intake_database_error():
    """Test create_intake with database error."""
    # Patch settings to return a URL for SUPABASE_URL
    with patch(
        "pi_auto_api.db.settings.SUPABASE_URL",
        "postgresql://test:test@localhost/testdb",
    ):
        # Patch asyncpg.connect to raise an exception
        with patch(
            "pi_auto_api.db.asyncpg.connect",
            side_effect=asyncpg.PostgresError("Database connection error"),
        ):
            payload = IntakePayload.model_validate(VALID_PAYLOAD)

            # Verify exception is propagated with a specific type
            with pytest.raises(asyncpg.PostgresError):
                await create_intake(payload)

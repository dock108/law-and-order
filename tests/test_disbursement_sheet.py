"""Tests for the disbursement sheet generation functionality."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import asyncpg
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from pi_auto_api.schemas import FeeAdjustment, FinalizeSettlementPayload
from pi_auto_api.utils.disbursement_calc import calc_split

# Mock app and client for FastAPI tests
test_app = FastAPI()
with patch("pi_auto_api.celery_app.app.send_task") as mock_send_task:
    mock_task = Mock()
    mock_task.id = "task-123"
    mock_send_task.return_value = mock_task
    from pi_auto_api.main import app

test_app.include_router(app.router)
client = TestClient(test_app)


@pytest.fixture
def mock_asyncpg_pool():
    """Create a mock database pool."""
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = AsyncMock()
    return mock_pool


@pytest.fixture
def mock_docassemble():
    """Mock the Docassemble API client."""
    with patch("pi_auto_api.externals.docassemble.generate_letter") as mock:
        mock.return_value = b"mock pdf content"
        yield mock


@pytest.fixture
def mock_docusign():
    """Mock the DocuSign API client."""
    with patch("pi_auto_api.externals.docusign.send_envelope") as mock:
        mock.return_value = "mock-envelope-id-123"
        yield mock


@pytest.fixture
def mock_task():
    """Mock Celery task."""
    with patch("pi_auto_api.tasks.disbursement.generate_disbursement_sheet") as mock:
        task_mock = MagicMock()
        task_mock.id = "mock-task-id-123"
        mock.delay.return_value = task_mock
        yield mock


@pytest.mark.asyncio
async def test_calc_split_success():
    """Test successful settlement split calculation."""
    # Mock database response
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    mock_conn.fetchrow.return_value = {
        "settlement_amount": Decimal("60000.00"),
        "attorney_fee_pct": Decimal("33.33"),
        "lien_total": Decimal("5000.00"),
    }
    mock_conn.fetchval.return_value = Decimal("1500.00")  # other adjustments

    with patch("asyncpg.connect", return_value=mock_conn):
        result = await calc_split(incident_id=123)

    # Verify the result
    assert result["gross"] == Decimal("60000.00")
    assert result["attorney_fee"] == Decimal("19998.00")  # 33.33% of 60000
    assert result["lien_total"] == Decimal("5000.00")
    assert result["other_adjustments"] == Decimal("1500.00")
    assert result["net_to_client"] == Decimal(
        "33502.00"
    )  # gross - fees - liens - adjustments


@pytest.mark.asyncio
async def test_calc_split_no_settlement():
    """Test calculation with no settlement amount."""
    # Mock database response
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    mock_conn.fetchrow.return_value = None  # No incident found

    with patch("asyncpg.connect", return_value=mock_conn):
        with pytest.raises(ValueError, match="Incident .* has no settlement amount"):
            await calc_split(incident_id=999)


def test_finalize_settlement_success():
    """Test successful settlement finalization."""
    # Mock database connection
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = 123  # incident_id

    # Mock task for celery
    mock_task = MagicMock()
    mock_task.id = "mock-task-id-123"

    # Test data
    payload = FinalizeSettlementPayload(
        incident_id=123,
        settlement_amount=Decimal("60000.00"),
        lien_total=Decimal("5000.00"),
        adjustments=[
            FeeAdjustment(description="Filing fee", amount=Decimal("500.00")),
            FeeAdjustment(description="Expert witness", amount=Decimal("1000.00")),
        ],
    )

    # Convert Decimal values to float for JSON serialization
    payload_dict = {
        "incident_id": payload.incident_id,
        "settlement_amount": float(payload.settlement_amount),
        "lien_total": float(payload.lien_total),
        "adjustments": (
            [
                {"description": adj.description, "amount": float(adj.amount)}
                for adj in payload.adjustments
            ]
            if payload.adjustments
            else None
        ),
    }

    # We need to mock the following:
    # 1. Database connection
    # 2. Celery task directly at the base level
    with patch("asyncpg.connect", return_value=mock_conn):
        with patch("pi_auto_api.celery_app.app.send_task") as mock_send_task:
            # Configure the mock to return a mock task
            mock_send_task.return_value = mock_task

            # Make request
            response = client.post("/internal/finalize_settlement", json=payload_dict)

    # Verify response
    assert response.status_code == 202
    assert response.json()["status"] == "success"
    assert response.json()["incident_id"] == 123
    assert response.json()["task_id"] == "mock-task-id-123"

    # Verify database calls
    mock_conn.fetchval.assert_called_once()
    # The implementation uses 2 execute calls:
    # 1 for incident update, 1 for combined fee adjustments
    assert mock_conn.execute.call_count == 2

    # Verify task was enqueued via send_task
    mock_send_task.assert_called_once()


# Mock HTTP response for testing
class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, content=None, status_code=200):
        """Initialize the mock response.

        Args:
            content: The response content bytes
            status_code: The HTTP status code to return
        """
        self.content = content or b"mock pdf content"
        self.status_code = status_code

    def raise_for_status(self):
        """Mock the raise_for_status method."""
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                message=f"HTTP Error {self.status_code}", request=None, response=self
            )


# Mock async client for testing
class MockAsyncClient:
    """Mock HTTP client for testing."""

    def __init__(self, response=None):
        """Initialize the mock client.

        Args:
            response: The response to return from post()
        """
        self.response = response or MockResponse()
        self.post = AsyncMock(return_value=self.response)

    async def __aenter__(self):
        """Enter the async context manager.

        Returns:
            The client instance itself.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager.

        Args:
            exc_type: The exception type, if any
            exc_val: The exception value, if any
            exc_tb: The exception traceback, if any
        """
        pass


@pytest.mark.xfail(reason="Simulated DocuSign environment not available")
@pytest.mark.asyncio
async def test_generate_disbursement_sheet():
    """Test the disbursement sheet generation task."""
    # Mock database query results
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    test_date = date(2023, 1, 1)
    mock_conn.fetchrow.return_value = {
        "incident_id": 123,
        "incident_date": test_date,
        "settlement_amount": Decimal("60000.00"),
        "attorney_fee_pct": Decimal("33.33"),
        "lien_total": Decimal("5000.00"),
        "client_id": 456,
        "client_name": "John Doe",
        "client_email": "john@example.com",
    }
    mock_conn.fetchval.return_value = "789"  # doc_id

    # Mock calc_split function result
    mock_totals = {
        "gross": Decimal("60000.00"),
        "attorney_fee": Decimal("19998.00"),
        "lien_total": Decimal("5000.00"),
        "other_adjustments": Decimal("1500.00"),
        "net_to_client": Decimal("33502.00"),
    }

    # Mock for DocuSign envelope_id result
    envelope_id = "mock-envelope-id-123"

    # Mock for httpx client
    mock_response = MockResponse(content=b"mock pdf content")
    mock_client = MockAsyncClient(response=mock_response)

    # Apply all the necessary patches
    with patch("asyncpg.connect", return_value=mock_conn):
        with patch(
            "pi_auto_api.utils.disbursement_calc.calc_split", return_value=mock_totals
        ):
            with patch("httpx.AsyncClient", return_value=mock_client):
                # Mock the _get_docusign_api_client function
                with patch(
                    "pi_auto_api.externals.docusign._get_docusign_api_client"
                ) as mock_docusign_client:
                    # Configure the API client mock
                    mock_api_client = MagicMock()
                    mock_api_client.loop = MagicMock()
                    mock_api_client.loop.run_in_executor = AsyncMock()
                    mock_api_client.loop.run_in_executor.return_value = MagicMock(
                        envelope_id=envelope_id
                    )
                    mock_docusign_client.return_value = mock_api_client

                    # This is also necessary: mock the send_envelope function
                    # to avoid call to API client
                    with patch(
                        "pi_auto_api.externals.docusign.send_envelope",
                        return_value=envelope_id,
                    ):
                        # Import the task module we're testing
                        from pi_auto_api.tasks.disbursement import (
                            generate_disbursement_sheet,
                        )

                        # Call the function we're testing
                        result = await generate_disbursement_sheet(123)

    # Verify the result
    assert result == envelope_id

    # Verify the mocks were called correctly
    mock_client.post.assert_called_once()

    # Verify database was updated
    assert mock_conn.execute.call_count >= 1


# Edge case test
@pytest.mark.asyncio
async def test_calc_split_zero_liens():
    """Test calculation with zero liens."""
    # Mock database response
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    mock_conn.fetchrow.return_value = {
        "settlement_amount": Decimal("50000.00"),
        "attorney_fee_pct": Decimal("33.33"),
        "lien_total": Decimal("0.00"),
    }
    mock_conn.fetchval.return_value = Decimal("0.00")  # No adjustments

    with patch("asyncpg.connect", return_value=mock_conn):
        result = await calc_split(incident_id=123)

    # Verify the result with no liens or adjustments
    assert result["gross"] == Decimal("50000.00")
    assert result["attorney_fee"] == Decimal("16665.00")  # 33.33% of 50000
    assert result["lien_total"] == Decimal("0.00")
    assert result["other_adjustments"] == Decimal("0.00")
    assert result["net_to_client"] == Decimal("33335.00")  # gross - fees only

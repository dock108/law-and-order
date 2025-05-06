"""Tests for the damages worksheet builder task."""

# import asyncio # Not directly used in tests
# import io # Not directly used in tests
from decimal import Decimal
from unittest.mock import AsyncMock, patch  # Removed MagicMock

import pandas as pd
import pytest
from pi_auto_api.config import settings
from pi_auto_api.tasks.damages import build_damages_worksheet


@pytest.fixture
def mock_db_connection_damages():
    """Mock database connection for damages worksheet tests."""
    mock_conn = AsyncMock()

    # Seed three medical bill docs
    mock_bill_records = [
        {
            "doc_id": 1,
            "provider_name": "City Hospital",
            "bill_url": "http://example.com/bill_city_100.50.pdf",
            "bill_amount": Decimal("100.50"),
            "bill_date": pd.Timestamp("2023-01-15"),
        },
        {
            "doc_id": 2,
            "provider_name": "Metro Clinic",
            "bill_url": "http://example.com/bill_metro_250.00.pdf",
            "bill_amount": Decimal("250.00"),
            "bill_date": pd.Timestamp("2023-01-20"),
        },
        {
            "doc_id": 3,
            "provider_name": "City Hospital",  # Same provider, different bill
            "bill_url": "http://example.com/bill_city_75.25.pdf",
            "bill_amount": Decimal("75.25"),
            "bill_date": pd.Timestamp("2023-02-01"),
        },
        {
            "doc_id": 4,  # Bill with null amount, to test parsing from URL
            "provider_name": "Urgent Care",
            "bill_url": "http://example.com/bill_urgent_123.45_details.pdf",
            "bill_amount": None,
            "bill_date": pd.Timestamp("2023-02-10"),
        },
    ]
    mock_conn.fetch.return_value = mock_bill_records
    mock_conn.execute.return_value = None  # For doc inserts
    return mock_conn


@pytest.mark.asyncio
async def test_build_damages_worksheet_success(mock_db_connection_damages):
    """Test successful generation of damages worksheet."""
    incident_id = 1
    expected_total_damages = 100.50 + 250.00 + 75.25 + 123.45  # Sum of all bills

    mock_excel_url = "https://supabase.example.com/excel_worksheet.xlsx"
    mock_pdf_url = "https://supabase.example.com/pdf_worksheet.pdf"

    with (
        patch("asyncpg.connect", return_value=mock_db_connection_damages),
        patch.object(settings, "SUPABASE_URL", "https://fake.supabase.co"),
        patch.object(settings, "SUPABASE_KEY", "fake-key"),
        patch(
            "pi_auto_api.tasks.damages.upload_to_bucket", new_callable=AsyncMock
        ) as mock_upload,
        patch("weasyprint.HTML.write_pdf") as mock_write_pdf,
    ):  # Fine to mock directly here
        mock_upload.side_effect = [
            mock_excel_url,
            mock_pdf_url,
        ]  # First call for excel, second for pdf
        mock_write_pdf.return_value = b"mock_pdf_bytes"

        result = await build_damages_worksheet(incident_id)

        assert result["status"] == "success"
        assert result["incident_id"] == incident_id
        assert pytest.approx(result["total_damages"]) == expected_total_damages
        assert result["excel_url"] == mock_excel_url
        assert result["pdf_url"] == mock_pdf_url

        # Check database calls
        mock_db_connection_damages.fetch.assert_called_once_with(
            """
        SELECT
            d.id AS doc_id,
            p.name AS provider_name,
            d.url AS bill_url,
            d.amount AS bill_amount,
            d.created_at AS bill_date
        FROM doc d
        JOIN provider p ON d.provider_id = p.id
        WHERE d.incident_id = $1 AND d.type = 'medical_bill'
        ORDER BY p.name, d.created_at;
        """,
            incident_id,
        )

        # Two uploads, two doc inserts
        assert mock_upload.call_count == 2
        assert mock_write_pdf.call_count == 1
        assert mock_db_connection_damages.execute.call_count == 2

        # Check doc insert calls (order of excel/pdf might vary, check types)
        first_doc_call = mock_db_connection_damages.execute.call_args_list[0][0]
        second_doc_call = mock_db_connection_damages.execute.call_args_list[1][0]

        doc_types_inserted = {first_doc_call[2], second_doc_call[2]}
        assert "damages_worksheet_excel" in doc_types_inserted
        assert "damages_worksheet_pdf" in doc_types_inserted

        if first_doc_call[2] == "damages_worksheet_excel":
            assert first_doc_call[3] == mock_excel_url
            assert second_doc_call[3] == mock_pdf_url
        else:
            assert first_doc_call[3] == mock_pdf_url
            assert second_doc_call[3] == mock_excel_url


@pytest.mark.asyncio
async def test_build_damages_worksheet_no_bills(mock_db_connection_damages):
    """Test behavior when no medical bills are found for an incident."""
    incident_id = 2
    mock_db_connection_damages.fetch.return_value = []  # Override to return no bills

    with patch(
        "asyncpg.connect", return_value=mock_db_connection_damages
    ):  # Only need to mock connection
        result = await build_damages_worksheet(incident_id)

    assert result["status"] == "no_bills"
    assert result["incident_id"] == incident_id
    assert result["total_damages"] == 0.0
    assert result["excel_url"] is None
    assert result["pdf_url"] is None
    mock_db_connection_damages.execute.assert_not_called()  # No docs should be inserted


@pytest.mark.asyncio
async def test_build_damages_worksheet_upload_failure(mock_db_connection_damages):
    """Test behavior when Supabase upload fails."""
    incident_id = 3

    with (
        patch("asyncpg.connect", return_value=mock_db_connection_damages),
        patch.object(settings, "SUPABASE_URL", "https://fake.supabase.co"),
        patch.object(settings, "SUPABASE_KEY", "fake-key"),
        patch(
            "pi_auto_api.tasks.damages.upload_to_bucket", new_callable=AsyncMock
        ) as mock_upload,
        patch("weasyprint.HTML.write_pdf") as mock_write_pdf,
    ):
        mock_upload.side_effect = Exception("Supabase boom!")  # Simulate upload failure
        mock_write_pdf.return_value = b"mock_pdf_bytes"

        result = await build_damages_worksheet(incident_id)

    assert result["status"] == "error"
    assert "Supabase boom!" in result["error"]
    assert (
        result["excel_url"] is None
    )  # Should be None as upload failed before assignment
    # pdf_url might or might not be None depending on when error happened
    # No docs should be inserted if upload fails
    mock_db_connection_damages.execute.assert_not_called()

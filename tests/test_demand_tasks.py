"""Tests for demand package assembly tasks."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pikepdf
import pytest

from pi_auto_api.tasks.demand import assemble_demand_package, check_and_build_demand


def create_sample_pdf() -> bytes:
    """Create a simple sample PDF document for testing."""
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(200, 200))

    out_stream = io.BytesIO()
    pdf.save(out_stream)
    out_stream.seek(0)
    return out_stream.getvalue()


@pytest.mark.asyncio
async def test_assemble_demand_package_success():
    """Test successful assembly of a demand package."""
    # Mock dependencies
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [
        {"id": "doc1", "type": "medical_records"},
        {"id": "doc2", "type": "damages_worksheet_pdf"},
        {"id": "doc3", "type": "liability_photo"},
    ]
    mock_conn.fetchval.return_value = "new_demand_package_id"

    sample_pdf = create_sample_pdf()

    # Patch dependencies
    with (
        patch("pi_auto_api.tasks.demand.is_demand_ready", AsyncMock(return_value=True)),
        patch(
            "pi_auto_api.tasks.demand.asyncpg.connect",
            AsyncMock(return_value=mock_conn),
        ),
        patch(
            "pi_auto_api.tasks.demand.get_file_content",
            AsyncMock(return_value=sample_pdf),
        ),
        patch("pi_auto_api.tasks.demand.upload_file", AsyncMock(return_value=True)),
        patch(
            "pi_auto_api.tasks.demand.merge_pdfs", MagicMock(return_value=sample_pdf)
        ),
    ):
        # Call the function
        result = await assemble_demand_package(incident_id=123)

        # Assertions
        assert result == "new_demand_package_id"
        mock_conn.fetch.assert_called_once()
        mock_conn.fetchval.assert_called_once()
        mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_assemble_demand_package_not_ready():
    """Test demand package assembly when incident is not ready."""
    # Patch dependencies
    with patch(
        "pi_auto_api.tasks.demand.is_demand_ready", AsyncMock(return_value=False)
    ):
        # Call the function
        result = await assemble_demand_package(incident_id=123)

        # Assertions
        assert result is None


@pytest.mark.asyncio
async def test_assemble_demand_package_upload_failure():
    """Test demand package assembly when upload fails."""
    # Mock dependencies
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [
        {"id": "doc1", "type": "medical_records"},
    ]
    mock_conn.fetchval.return_value = "new_demand_package_id"

    sample_pdf = create_sample_pdf()

    # Patch dependencies
    with (
        patch("pi_auto_api.tasks.demand.is_demand_ready", AsyncMock(return_value=True)),
        patch(
            "pi_auto_api.tasks.demand.asyncpg.connect",
            AsyncMock(return_value=mock_conn),
        ),
        patch(
            "pi_auto_api.tasks.demand.get_file_content",
            AsyncMock(return_value=sample_pdf),
        ),
        patch("pi_auto_api.tasks.demand.upload_file", AsyncMock(return_value=False)),
        patch(
            "pi_auto_api.tasks.demand.merge_pdfs", MagicMock(return_value=sample_pdf)
        ),
    ):
        # Call the function
        result = await assemble_demand_package(incident_id=123)

        # Assertions
        assert result is None
        mock_conn.execute.assert_called_once()  # Should delete the document record


@pytest.mark.asyncio
async def test_check_and_build_demand_no_incidents():
    """Test nightly check with no incidents found."""
    # Mock dependencies
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []

    # Patch dependencies
    with patch(
        "pi_auto_api.tasks.demand.asyncpg.connect", AsyncMock(return_value=mock_conn)
    ):
        # Call the function
        result = await check_and_build_demand()

        # Assertions
        assert result == 0
        mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_check_and_build_demand_with_eligible_incidents():
    """Test nightly check with eligible incidents."""
    # Mock dependencies
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [{"id": 123}, {"id": 456}]

    # Patch dependencies
    with (
        patch(
            "pi_auto_api.tasks.demand.asyncpg.connect",
            AsyncMock(return_value=mock_conn),
        ),
        patch(
            "pi_auto_api.tasks.demand.is_demand_ready",
            AsyncMock(side_effect=[True, False]),
        ),
        patch(
            "pi_auto_api.tasks.demand.assemble_demand_package",
            AsyncMock(return_value="demand_id"),
        ) as mock_assemble_demand_package,
    ):
        # Call the function
        result = await check_and_build_demand()

        # Assertions
        assert result == 1  # Only one package should be created
        assert mock_assemble_demand_package.called
        assert mock_assemble_demand_package.call_count == 1

"""Tests for PDF merge utility functions."""

import io

import pikepdf
import pytest

from pi_auto_api.utils.pdf_merge import merge_pdfs


def create_sample_pdf() -> bytes:
    """Create a simple sample PDF document for testing."""
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(200, 200))

    out_stream = io.BytesIO()
    pdf.save(out_stream)
    out_stream.seek(0)
    return out_stream.getvalue()


@pytest.fixture
def sample_pdfs():
    """Create a list of sample PDF documents for testing."""
    return [create_sample_pdf() for _ in range(3)]


def test_merge_pdfs_success(sample_pdfs):
    """Test successful merging of multiple PDFs."""
    merged_pdf_bytes = merge_pdfs(sample_pdfs)

    # Verify the result is valid PDF bytes
    assert merged_pdf_bytes
    assert isinstance(merged_pdf_bytes, bytes)

    # Verify it contains the expected number of pages
    with pikepdf.Pdf.open(io.BytesIO(merged_pdf_bytes)) as pdf:
        assert len(pdf.pages) == 3


def test_merge_pdfs_empty_list():
    """Test merging an empty list of PDFs raises ValueError."""
    with pytest.raises(ValueError, match="Cannot merge an empty list of PDFs"):
        merge_pdfs([])


def test_merge_pdfs_invalid_pdf():
    """Test merging invalid PDF data raises PdfError."""
    invalid_data = b"This is not a valid PDF file"

    with pytest.raises(pikepdf.PdfError):
        merge_pdfs([invalid_data])


def test_merge_pdfs_mixed_valid_invalid():
    """Test merging a mix of valid and invalid PDFs."""
    valid_pdf = create_sample_pdf()
    invalid_data = b"This is not a valid PDF file"

    with pytest.raises(pikepdf.PdfError):
        merge_pdfs([valid_pdf, invalid_data])

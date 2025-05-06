"""Utility functions for merging PDF documents."""

import io
import logging

import pikepdf

logger = logging.getLogger(__name__)


def merge_pdfs(list_of_pdf_bytes: list[bytes]) -> bytes:
    """Merge multiple PDF documents (provided as bytes) into a single PDF.

    Args:
        list_of_pdf_bytes: A list where each element is the byte content of a PDF.

    Returns:
        Bytes of the merged PDF document.

    Raises:
        pikepdf.PdfError: If any of the inputs are not valid PDFs or merging fails.
        ValueError: If the list_of_pdf_bytes is empty.
    """
    if not list_of_pdf_bytes:
        raise ValueError("Cannot merge an empty list of PDFs.")

    merged_pdf = pikepdf.Pdf.new()

    for i, pdf_bytes in enumerate(list_of_pdf_bytes):
        try:
            with pikepdf.Pdf.open(io.BytesIO(pdf_bytes)) as pdf_doc:
                merged_pdf.pages.extend(pdf_doc.pages)
        except Exception as e:
            logger.error(f"Error processing PDF document at index {i}: {e}")
            # Optionally, re-raise a more specific error or handle it
            raise pikepdf.PdfError(
                f"Failed to process or merge PDF at index {i}. Error: {e}"
            ) from e

    output_io = io.BytesIO()
    merged_pdf.save(output_io)
    return output_io.getvalue()

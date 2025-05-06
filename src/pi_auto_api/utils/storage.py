"""Storage utilities for handling file uploads and downloads."""

import logging
import uuid
from datetime import datetime

import httpx
from fastapi import HTTPException, status

from pi_auto_api.config import settings

logger = logging.getLogger(__name__)


async def upload_to_bucket(pdf_bytes: bytes) -> str:
    """Upload a PDF to Supabase Storage and return a signed URL valid for 24 hours.

    Args:
        pdf_bytes: Raw bytes of the PDF to upload

    Returns:
        A signed media URL valid for 24 hours (required by Twilio Fax)

    Raises:
        HTTPException: If the upload fails or URL signing fails
        ValueError: If Supabase credentials are not configured
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.error("Supabase credentials not configured")
        raise ValueError("Supabase credentials not configured")

    # Generate a unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"medical_records_request_{timestamp}_{uuid.uuid4()}.pdf"

    bucket_name = "documents"
    object_path = f"medical_records/{filename}"

    # API endpoints
    upload_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/{bucket_name}/{object_path}"
    )
    sign_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/sign/{bucket_name}/{object_path}"
    )

    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/pdf",
    }

    async with httpx.AsyncClient() as client:
        try:
            # Upload the PDF to Supabase Storage
            upload_response = await client.post(
                upload_url, content=pdf_bytes, headers=headers, timeout=30.0
            )
            upload_response.raise_for_status()

            # Generate a signed URL valid for 24 hours
            expires_in = 60 * 60 * 24  # 24 hours in seconds
            sign_response = await client.post(
                sign_url, json={"expiresIn": expires_in}, headers=headers, timeout=10.0
            )
            sign_response.raise_for_status()

            signed_url = sign_response.json().get("signedURL")
            if not signed_url:
                raise ValueError("No signed URL returned from Supabase")

            # Make sure the URL is publicly accessible (required by Twilio)
            signed_url = (
                signed_url
                if signed_url.startswith("http")
                else f"{settings.SUPABASE_URL}{signed_url}"
            )

            logger.info(f"Successfully uploaded and signed URL for {object_path}")
            return signed_url

        except httpx.RequestError as exc:
            logger.error(f"Error uploading to Supabase Storage: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error uploading document: {exc}",
            ) from exc
        except httpx.HTTPStatusError as exc:
            status_code = (
                status.HTTP_400_BAD_REQUEST
                if 400 <= exc.response.status_code < 500
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            detail = (
                f"Supabase Storage API error ({exc.response.status_code}): "
                f"{exc.response.text}"
            )
            logger.error(detail, exc_info=True)
            raise HTTPException(status_code=status_code, detail=detail) from exc
        except Exception as exc:
            logger.error(f"Unexpected error in storage operation: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {exc}",
            ) from exc


async def upload_file(doc_id: str, content_bytes: bytes, content_type: str) -> bool:
    """Upload a file to Supabase Storage under a specific doc_id.

    Args:
        doc_id: The unique ID of the document, used as the filename.
        content_bytes: Raw bytes of the file to upload.
        content_type: The MIME type of the file (e.g., 'application/pdf').

    Returns:
        True if upload was successful, False otherwise.

    Raises:
        ValueError: If Supabase credentials are not configured.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.error("Supabase credentials not configured for upload_file")
        raise ValueError("Supabase credentials not configured for upload_file")

    bucket_name = "documents"  # Or your general documents bucket
    # Using doc_id as the filename to ensure uniqueness and direct relation
    object_path = f"generated/{doc_id}"

    upload_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/{bucket_name}/{object_path}"
    )
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": content_type,
    }

    async with httpx.AsyncClient() as client:
        try:
            upload_response = await client.post(
                upload_url, content=content_bytes, headers=headers, timeout=30.0
            )
            upload_response.raise_for_status()
            logger.info(f"Successfully uploaded file {doc_id} to {object_path}")
            return True
        except httpx.RequestError as exc:
            logger.error(
                f"Error uploading file {doc_id} to Supabase: {exc}", exc_info=True
            )
            return False
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Supabase API error for {doc_id} ({exc.response.status_code}): "
                f"{exc.response.text}",
                exc_info=True,
            )
            return False
        except Exception as exc:
            logger.error(
                f"Unexpected error uploading file {doc_id}: {exc}", exc_info=True
            )
            return False


async def get_file_content(doc_id: str) -> bytes | None:
    """Retrieve the content of a file from Supabase Storage using its doc_id.

    Assumes the file was stored using the doc_id as its name in a 'generated' path.

    Args:
        doc_id: The unique ID of the document (used as filename).

    Returns:
        The file content as bytes if successful, None otherwise.

    Raises:
        ValueError: If Supabase credentials are not configured.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.error("Supabase credentials not configured for get_file_content")
        raise ValueError("Supabase credentials not configured for get_file_content")

    bucket_name = "documents"
    object_path = f"generated/{doc_id}"  # Assuming files are stored here by upload_file

    download_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/{bucket_name}/{object_path}"
    )
    headers = {"Authorization": f"Bearer {settings.SUPABASE_KEY}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(download_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            logger.info(f"Successfully retrieved file content for {doc_id}")
            return response.content
        except httpx.RequestError as exc:
            logger.error(
                f"Error downloading file {doc_id} from Supabase: {exc}", exc_info=True
            )
            return None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.warning(f"File {doc_id} not found in Supabase at {object_path}.")
            else:
                logger.error(
                    f"Supabase API error for {doc_id} ({exc.response.status_code}): "
                    f"{exc.response.text}",
                    exc_info=True,
                )
            return None
        except Exception as exc:
            logger.error(
                f"Unexpected error downloading file {doc_id}: {exc}", exc_info=True
            )
            return None

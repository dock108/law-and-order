"""Client for interacting with the Docassemble API."""

import httpx
from fastapi import HTTPException, status

from pi_auto_api.config import settings


async def generate_retainer_pdf(payload: dict) -> bytes:
    """Generate a retainer PDF using the Docassemble API.

    Args:
        payload: Data payload required by the Docassemble interview.

    Returns:
        Raw bytes of the generated PDF document.

    Raises:
        HTTPException: If the Docassemble API call fails.
    """
    api_url = f"{settings.DOCASSEMBLE_URL}/api/v1/generate/retainer"
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                api_url, json=payload, headers=headers, timeout=60.0
            )
            response.raise_for_status()  # Raise exception for 4xx or 5xx responses
            return response.content
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error contacting Docassemble API: {exc}",
            ) from exc
        except httpx.HTTPStatusError as exc:
            status_code = (
                status.HTTP_400_BAD_REQUEST
                if 400 <= exc.response.status_code < 500
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            detail = (
                f"Docassemble API error ({exc.response.status_code}): "
                f"{exc.response.text}"
            )
            # Raise HTTPException, linking the original exception
            raise HTTPException(status_code=status_code, detail=detail) from exc

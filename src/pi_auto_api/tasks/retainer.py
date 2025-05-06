"""Tasks for generating retainer agreements and handling e-signatures."""

import asyncio
import logging

from pi_auto_api.celery_app import app
from pi_auto_api.db import get_client_payload
from pi_auto_api.externals.docassemble import generate_retainer_pdf
from pi_auto_api.externals.docusign import send_envelope

logger = logging.getLogger(__name__)


async def _run_retainer_flow(client_id: int):
    """Helper async function containing the core retainer generation logic."""
    # 1. Fetch data from DB
    logger.info(f"Fetching payload for client_id: {client_id}")
    payload = await get_client_payload(client_id)
    logger.info(f"Payload fetched successfully for client_id: {client_id}")

    # 2. Call Docassemble API to generate the PDF
    logger.info(f"Generating PDF via Docassemble for client_id: {client_id}")
    pdf_bytes = await generate_retainer_pdf(payload)
    logger.info(f"PDF generated successfully for client_id: {client_id}")

    # 3. Create a DocuSign envelope and email it
    client_email = payload["client"]["email"]
    client_name = payload["client"]["full_name"]
    logger.info(
        f"Sending DocuSign envelope to {client_email} for client_id: {client_id}"
    )
    envelope_id = await send_envelope(pdf_bytes, client_email, client_name)
    logger.info(f"Envelope {envelope_id} sent successfully for client_id: {client_id}")

    # TODO: Update database task status here (e.g., client.task table)

    return {"client_id": client_id, "envelope_id": envelope_id, "status": "completed"}


@app.task(name="generate_retainer", bind=True)
def generate_retainer(self, client_id: int):
    """Generate retainer agreement, send for e-signature, and update status.

    Fetches client/incident data, generates PDF via Docassemble,
    sends PDF for signature via DocuSign, and updates task status.

    Args:
        self: The Celery task instance (automatically passed with bind=True).
        client_id: The ID of the client for whom to generate the retainer.

    Returns:
        A dictionary containing the client_id and the DocuSign envelope_id.

    Raises:
        Exception: Propagates exceptions from DB or external API calls.
    """
    logger.info(f"Starting retainer generation for client_id: {client_id}")
    try:
        # Always run the async helper in a new event loop for the task context
        result = asyncio.run(_run_retainer_flow(client_id))
        return result

    except Exception as exc:
        logger.error(
            f"Retainer generation failed for client_id: {client_id}. Error: {exc}",
            exc_info=True,
        )
        # Reraise the exception to mark the task as failed
        # Use exponential backoff for retries
        # Add 'from exc' to satisfy B904, though Celery handles the cause implicitly.
        raise self.retry(
            exc=exc, countdown=60 * (self.request.retries + 1), max_retries=3
        ) from exc

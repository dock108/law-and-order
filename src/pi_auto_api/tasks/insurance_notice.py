"""Tasks for sending Letter of Representation to insurance carriers."""

import asyncio
import logging

from pi_auto_api.db import get_insurance_payload
from pi_auto_api.externals.docassemble import generate_letter
from pi_auto_api.externals.sendgrid_client import send_mail
from pi_auto_api.externals.twilio_client import send_fax
from pi_auto_api.tasks import app

logger = logging.getLogger(__name__)


async def _run_insurance_notice_flow(client_id: int):
    """Helper async function containing the LOR generation and distribution logic.

    Args:
        client_id: The ID of the client

    Returns:
        Dictionary with task status and details
    """
    # 1. Fetch insurance data from DB
    logger.info(f"Fetching insurance payload for client_id: {client_id}")
    payload = await get_insurance_payload(client_id)
    logger.info(f"Insurance payload fetched successfully for client_id: {client_id}")

    # 2. Call Docassemble API to generate the LOR PDF
    logger.info(f"Generating LOR PDF via Docassemble for client_id: {client_id}")
    await generate_letter("lor", payload)
    logger.info(f"LOR PDF generated successfully for client_id: {client_id}")

    # Store results for reporting
    results = {"client_id": client_id, "faxes_sent": [], "emails_sent": []}

    # 3. Process client insurance if available
    if payload.get("client_insurance") and payload["client_insurance"].get(
        "carrier_name"
    ):
        client_carrier = payload["client_insurance"]["carrier_name"]
        logger.info(f"Processing client insurance: {client_carrier}")

        # TODO: In a real implementation, you would upload the PDF to a temporary
        # location and get a public URL for the fax API. For testing, we'll mock this.
        mock_pdf_url = f"https://example.com/temp/lor_{client_id}_client.pdf"

        # Send fax to client insurance if we have their info
        # In a real implementation, you would get the fax number from insurance db
        mock_fax_number = "+15551234567"  # This would come from the database

        try:
            fax_sid = await send_fax(to=mock_fax_number, media_url=mock_pdf_url)
            results["faxes_sent"].append(
                {
                    "carrier": client_carrier,
                    "fax_number": mock_fax_number,
                    "status": "sent",
                    "sid": fax_sid,
                }
            )
            logger.info(f"Fax sent successfully to client carrier {client_carrier}")
        except Exception as e:
            logger.error(f"Error sending fax to client carrier: {str(e)}")
            results["faxes_sent"].append(
                {
                    "carrier": client_carrier,
                    "fax_number": mock_fax_number,
                    "status": "failed",
                    "error": str(e),
                }
            )

    # 4. Process adverse insurance carriers
    for insurance in payload.get("adverse_insurance", []):
        carrier = insurance.get("carrier_name")
        if not carrier:
            continue

        logger.info(f"Processing adverse insurance: {carrier}")

        # Mock PDF URL for the fax API
        mock_pdf_url = f"https://example.com/temp/lor_{client_id}_{carrier}.pdf"

        # Send fax to adverse insurance
        mock_fax_number = "+15559876543"  # This would come from the database

        try:
            fax_sid = await send_fax(to=mock_fax_number, media_url=mock_pdf_url)
            results["faxes_sent"].append(
                {
                    "carrier": carrier,
                    "fax_number": mock_fax_number,
                    "status": "sent",
                    "sid": fax_sid,
                }
            )
            logger.info(f"Fax sent successfully to adverse carrier {carrier}")

            # If we have adjuster email, send email as well
            # In a real implementation, you would get the email from insurance db
            mock_adjuster_email = (
                "adjuster@example.com"  # This would come from the database
            )

            try:
                message_id = await send_mail(
                    # This would be a specific LOR template
                    template_name="retainer_sent.html",
                    to_email=mock_adjuster_email,
                    template_ctx={
                        "client": payload["client"],
                        "support_email": "support@piautolaw.com",
                        "support_phone": "(555) 123-4567",
                    },
                )
                results["emails_sent"].append(
                    {
                        "carrier": carrier,
                        "email": mock_adjuster_email,
                        "status": "sent",
                        "message_id": message_id,
                    }
                )
                logger.info(f"Email sent successfully to adjuster at {carrier}")
            except Exception as e:
                logger.error(f"Error sending email to adjuster: {str(e)}")
                results["emails_sent"].append(
                    {
                        "carrier": carrier,
                        "email": mock_adjuster_email,
                        "status": "failed",
                        "error": str(e),
                    }
                )
        except Exception as e:
            logger.error(f"Error sending fax to adverse carrier: {str(e)}")
            results["faxes_sent"].append(
                {
                    "carrier": carrier,
                    "fax_number": mock_fax_number,
                    "status": "failed",
                    "error": str(e),
                }
            )

    # 5. TODO: Update database task status here (e.g., mark LOR as sent)

    return results


@app.task(name="send_insurance_notice", bind=True)
def send_insurance_notice(self, client_id: int):
    """Generate and send Letter of Representation to insurance carriers.

    Fetches client/insurance data, generates LOR via Docassemble,
    sends fax to carriers via Twilio, and emails adjusters if available.

    Args:
        self: The Celery task instance (automatically passed with bind=True)
        client_id: The ID of the client

    Returns:
        A dictionary containing results of the fax/email operations

    Raises:
        Exception: Propagates exceptions from DB or external API calls
    """
    logger.info(f"Starting insurance notice for client_id: {client_id}")
    try:
        # Always run the async helper in a new event loop for the task context
        result = asyncio.run(_run_insurance_notice_flow(client_id))
        return result
    except Exception as exc:
        logger.error(
            f"Insurance notice failed for client_id: {client_id}. Error: {exc}",
            exc_info=True,
        )
        # Reraise the exception to mark the task as failed
        # Use exponential backoff for retries
        raise self.retry(
            exc=exc, countdown=60 * (self.request.retries + 1), max_retries=3
        ) from exc

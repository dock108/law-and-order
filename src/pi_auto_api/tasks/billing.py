"""Tasks related to billing and financial documents."""

import logging
from typing import Any, Dict, Optional

import asyncpg

from pi_auto_api.config import settings
from pi_auto_api.tasks import app
from pi_auto_api.tasks.damages import (
    build_damages_worksheet,  # Uncommented and corrected
)

logger = logging.getLogger(__name__)


@app.task(name="process_medical_bill")
async def process_medical_bill(
    incident_id: int,
    provider_id: int,
    document_url: str,
    amount: Optional[float] = None,
    # Potentially other metadata like service dates, bill date etc.
) -> Dict[str, Any]:
    """Process an uploaded medical bill, create a doc row, and trigger damages ws.

    Args:
        incident_id: The ID of the incident the bill belongs to.
        provider_id: The ID of the provider who issued the bill.
        document_url: The URL of the uploaded bill PDF.
        amount: The total amount of the bill (if known, otherwise parsed from PDF name).

    Returns:
        A dictionary containing the ID of the created doc row and worksheet status.
    """
    conn = None
    doc_id = None
    worksheet_task_id: Optional[str] = None  # Ensure it is Optional[str]

    logger.info(
        f"Processing medical bill for incident {incident_id}, "
        f"provider {provider_id} at {document_url}"
    )

    # 1. Parse amount from filename if not provided (placeholder logic)
    parsed_amount = amount
    if parsed_amount is None:
        # Placeholder: Attempt to parse from document_url or filename
        # e.g., if filename is "bill_123.45_details.pdf"
        try:
            # This is a very naive parsing attempt, robust parsing is complex
            filename_parts = document_url.split("_")
            for part in filename_parts:
                if "." in part:
                    potential_amount = part.split(".")[0] + "." + part.split(".")[1][:2]
                    if all(c.isdigit() or c == "." for c in potential_amount):
                        parsed_amount = float(potential_amount)
                        logger.info(f"Parsed amount {parsed_amount} from URL.")
                        break
            if parsed_amount is None:
                logger.warning("Could not parse amount from document URL, using 0.0")
                parsed_amount = 0.0  # Default if not parsable
        except Exception as e:
            logger.error(f"Error parsing amount from URL {document_url}: {e}")
            parsed_amount = 0.0  # Default on error

    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # 2. Insert 'medical_bill' doc row
        insert_query = """
        INSERT INTO doc (
            incident_id, provider_id, type, url, status, amount, created_at
        )
        VALUES ($1, $2, 'medical_bill', $3, 'received', $4, NOW())
        RETURNING id
        """
        doc_id = await conn.fetchval(
            insert_query,
            incident_id,
            provider_id,
            document_url,
            parsed_amount,
        )
        logger.info(f"Created medical_bill doc row with ID: {doc_id}")

        # 3. Trigger damages worksheet build
        worksheet_task = build_damages_worksheet.delay(incident_id)
        worksheet_task_id = worksheet_task.id
        logger.info(
            f"Queued build_damages_worksheet task {worksheet_task_id} "
            f"for incident {incident_id}"
        )

        return {
            "doc_id": doc_id,
            "status": "processed",
            "amount_recorded": parsed_amount,
            "worksheet_task_id": worksheet_task_id,
        }

    except Exception as e:
        logger.error(
            f"Error processing medical bill for incident {incident_id}: {e}",
            exc_info=True,
        )
        return {
            "doc_id": doc_id,
            "status": "error",
            "error": str(e),
            "amount_recorded": parsed_amount,
            "worksheet_task_id": worksheet_task_id,
        }
    finally:
        if conn:
            await conn.close()

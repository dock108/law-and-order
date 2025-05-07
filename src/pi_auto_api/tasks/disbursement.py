"""Celery tasks for generating and managing settlement disbursement sheets."""

import logging
from datetime import datetime
from typing import Optional

import asyncpg

from pi_auto_api.celery_app import app
from pi_auto_api.config import settings
from pi_auto_api.events import record_event
from pi_auto_api.externals.docassemble import generate_letter
from pi_auto_api.externals.docusign import send_envelope
from pi_auto_api.utils.disbursement_calc import calc_split

logger = logging.getLogger(__name__)


@app.task(name="generate_disbursement_sheet")
async def generate_disbursement_sheet(incident_id: int) -> Optional[str]:
    """Generate a disbursement sheet for a settled incident.

    Args:
        incident_id: The ID of the incident to generate a disbursement sheet for.

    Returns:
        The DocuSign envelope ID if successful, None otherwise.
    """
    conn = None
    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Fetch incident and client details
        query = """
        SELECT
            i.id as incident_id,
            i.date as incident_date,
            i.settlement_amount,
            i.attorney_fee_pct,
            i.lien_total,
            c.id as client_id,
            c.full_name as client_name,
            c.email as client_email
        FROM incident i
        JOIN client c ON i.client_id = c.id
        WHERE i.id = $1
        """
        row = await conn.fetchrow(query, incident_id)

        if not row or not row["settlement_amount"]:
            logger.error(
                f"Incident {incident_id} not found or has no settlement amount"
            )
            return None

        # Calculate the settlement split
        try:
            totals = await calc_split(incident_id)
        except ValueError as e:
            logger.error(f"Error calculating split for incident {incident_id}: {e}")
            return None

        # Prepare payload for Docassemble
        payload = {
            "client": {
                "id": row["client_id"],
                "full_name": row["client_name"],
                "email": row["client_email"],
            },
            "incident": {
                "id": row["incident_id"],
                "date": (
                    row["incident_date"].isoformat() if row["incident_date"] else None
                ),
                "attorney_fee_pct": float(row["attorney_fee_pct"]),
            },
            "totals": {
                "gross": float(totals["gross"]),
                "attorney_fee": float(totals["attorney_fee"]),
                "lien_total": float(totals["lien_total"]),
                "other_adjustments": float(totals["other_adjustments"]),
                "net_to_client": float(totals["net_to_client"]),
            },
        }

        # Generate the PDF using Docassemble
        try:
            pdf_bytes = await generate_letter("disbursement", payload)
        except Exception as e:
            logger.error(f"Error generating disbursement sheet PDF: {e}", exc_info=True)
            return None

        # Send the PDF for e-signature via DocuSign
        try:
            envelope_id = await send_envelope(
                pdf_bytes,
                client_email=row["client_email"],
                client_name=row["client_name"],
            )
        except Exception as e:
            logger.error(
                f"Error sending disbursement sheet for signature: {e}", exc_info=True
            )
            return None

        # Update the incident status to 'sent'
        update_query = """
        UPDATE incident
        SET disbursement_status = 'sent'
        WHERE id = $1
        """
        await conn.execute(update_query, incident_id)

        # Insert a new document record
        doc_query = """
        INSERT INTO doc (incident_id, type, url, status, created_at)
        VALUES ($1, 'disbursement_sheet', $2, 'sent', $3)
        RETURNING id
        """
        doc_url = f"envelope:{envelope_id}"
        doc_id = await conn.fetchval(doc_query, incident_id, doc_url, datetime.now())

        logger.info(
            f"Disbursement sheet generated and sent for incident {incident_id}, "
            f"envelope_id: {envelope_id}, doc_id: {doc_id}"
        )

        # Record event after successful generation and sending
        await record_event(
            {
                "type": "disbursement_sent",
                "incident_id": incident_id,
                "envelope_id": envelope_id,
                "doc_id": doc_id,
            }
        )

        return envelope_id

    except Exception as e:
        logger.error(
            f"Error generating disbursement sheet for incident {incident_id}: {e}",
            exc_info=True,
        )
        return None
    finally:
        if conn:
            await conn.close()

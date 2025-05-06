"""Task for sending medical record requests to healthcare providers."""

from typing import Dict

import asyncpg
from celery.utils.log import get_task_logger

from pi_auto_api.celery_app import app
from pi_auto_api.config import settings
from pi_auto_api.db import get_provider_payload
from pi_auto_api.externals.docassemble import generate_letter
from pi_auto_api.externals.twilio_client import send_fax
from pi_auto_api.utils.storage import upload_to_bucket

# Use the Celery logger for tasks
logger = get_task_logger(__name__)


@app.task(name="send_medical_record_requests")
async def send_medical_record_requests() -> Dict[str, int]:
    """Send medical record requests to providers who haven't sent records yet.

    For each provider lacking a 'records_request_sent' document:
    1. Build a provider payload
    2. Generate a medical records request letter
    3. Upload the PDF to Supabase storage
    4. Send a fax to the provider
    5. Record the request in the database

    Returns:
        Dictionary with count of faxes queued
    """
    conn = None
    fax_count = 0

    try:
        # Connect to the database
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Find incidents with providers who haven't sent records yet
        query = """
        SELECT
            i.id AS incident_id,
            p.id AS provider_id,
            p.name AS provider_name,
            p.fax AS provider_fax
        FROM incident i
        JOIN provider p ON p.incident_id = i.id
        WHERE p.status <> 'records_received'
        AND NOT EXISTS (
            SELECT 1 FROM document d
            WHERE d.provider_id = p.id
            AND d.type = 'records_request_sent'
        )
        """

        pending_providers = await conn.fetch(query)
        logger.info(
            f"Found {len(pending_providers)} providers needing medical records requests"
        )

        for provider in pending_providers:
            try:
                # 1. Build provider payload
                payload = await get_provider_payload(
                    provider["incident_id"], provider["provider_id"]
                )

                # 2. Generate the medical records request letter
                pdf_bytes = await generate_letter("medical_records_request", payload)

                # 3. Upload the PDF to storage
                media_url = await upload_to_bucket(pdf_bytes)

                # 4. Send the fax to the provider
                fax_sid = await send_fax(provider["provider_fax"], media_url)

                # 5. Record the request in the database
                insert_query = """
                INSERT INTO document (
                    incident_id, provider_id, type, url, status,
                    external_id, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """
                await conn.execute(
                    insert_query,
                    provider["incident_id"],
                    provider["provider_id"],
                    "records_request_sent",
                    media_url,
                    "sent",
                    fax_sid,
                )

                logger.info(
                    f"Successfully sent medical records request to "
                    f"provider ID {provider['provider_id']} "
                    f"({provider['provider_name']})"
                )

                fax_count += 1

            except Exception as e:
                logger.error(
                    f"Error sending medical records request to provider ID "
                    f"{provider['provider_id']}: {str(e)}",
                    exc_info=True,
                )
                # Continue with the next provider even if one fails
                continue

        return {"queued": fax_count}

    except Exception as e:
        logger.error(f"Error in medical records request task: {str(e)}", exc_info=True)
        return {"queued": 0}  # Return 0 on error instead of raising

    finally:
        if conn:
            await conn.close()

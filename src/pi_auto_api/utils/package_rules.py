"""Utility functions for checking if a demand package is ready to be assembled."""

import logging

import asyncpg

from pi_auto_api.config import settings

logger = logging.getLogger(__name__)


async def is_demand_ready(incident_id: int) -> bool:
    """Check if all required documents for a demand package are present for an incident.

    Args:
        incident_id: The ID of the incident.

    Returns:
        True if all conditions are met, False otherwise.
    """
    conn = None
    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Check for medical_records, damages_worksheet_pdf, and liability_photo
        # Also checks if a demand_package already exists
        doc_types_query = """
        SELECT
            EXISTS(SELECT 1 FROM doc
                   WHERE incident_id = $1 AND type = 'medical_records')
                   AS has_medical_records,
            EXISTS(SELECT 1 FROM doc
                   WHERE incident_id = $1 AND type = 'damages_worksheet_pdf')
                   AS has_damages_worksheet_pdf,
            EXISTS(SELECT 1 FROM doc
                   WHERE incident_id = $1 AND type = 'liability_photo')
                   AS has_liability_photo,
            NOT EXISTS(SELECT 1 FROM doc
                       WHERE incident_id = $1 AND type = 'demand_package')
                       AS no_existing_demand_package;
        """
        doc_types_check = await conn.fetchrow(doc_types_query, incident_id)

        if not doc_types_check or not all(
            [
                doc_types_check["has_medical_records"],
                doc_types_check["has_damages_worksheet_pdf"],
                doc_types_check["has_liability_photo"],
                doc_types_check["no_existing_demand_package"],
            ]
        ):
            logger.info(
                f"Incident {incident_id}: Missing required docs or pkg exists. "
                f"Details: {doc_types_check}"
            )
            return False

        # Check if all providers associated with the incident
        # have at least one medical bill
        all_providers_have_bills_query = """
        SELECT COALESCE(
            (
                SELECT bool_and(EXISTS(
                    SELECT 1 FROM doc d_bill
                    WHERE d_bill.incident_id = d_prov.incident_id
                      AND d_bill.provider_id = d_prov.provider_id
                      AND d_bill.type = 'medical_bill'
                ))
                FROM (
                    SELECT DISTINCT
                        incident_id,
                        provider_id  # noqa: E501
                    FROM doc
                    WHERE incident_id = $1 AND provider_id IS NOT NULL
                )
                AS d_prov
            ),
            TRUE -- If no providers associated, condition is met.
        ) AS all_providers_have_bills;
        """

        providers_check = await conn.fetchval(
            all_providers_have_bills_query, incident_id
        )

        if not providers_check:
            logger.info(
                f"Incident {incident_id}: Not all providers have medical bills logged."
            )
            return False

        logger.info(f"Incident {incident_id}: All conditions for demand package met.")
        return True

    except Exception as e:
        logger.error(
            f"Error checking demand readiness for incident {incident_id}: {e}",
            exc_info=True,
        )
        return False
    finally:
        if conn:
            await conn.close()

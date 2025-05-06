"""Utilities for calculating settlement disbursement splits."""

import logging
from decimal import Decimal
from typing import Dict

import asyncpg

from pi_auto_api.config import settings

logger = logging.getLogger(__name__)


async def calc_split(incident_id: int) -> Dict[str, Decimal]:
    """Calculate the split of a settlement amount for an incident.

    Args:
        incident_id: The ID of the incident to calculate the split for.

    Returns:
        A dictionary containing the settlement split amounts:
        {
            "gross": 60000,
            "attorney_fee": 20000,
            "lien_total": 5000,
            "other_adjustments": 1500,
            "net_to_client": 33500
        }

    Raises:
        ValueError: If the incident doesn't have a settlement amount or
                  if there's an error in the calculation.
    """
    conn = None
    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Get settlement details from the incident
        incident_query = """
        SELECT
            settlement_amount,
            attorney_fee_pct,
            lien_total
        FROM incident
        WHERE id = $1
        """
        incident = await conn.fetchrow(incident_query, incident_id)

        if not incident or not incident["settlement_amount"]:
            raise ValueError(f"Incident {incident_id} has no settlement amount")

        # Get fee adjustments for the incident
        adjustments_query = """
        SELECT SUM(amount) as total_adjustments
        FROM fee_adjustments
        WHERE incident_id = $1
        """
        adjustments = await conn.fetchval(adjustments_query, incident_id)

        # Calculate the split
        gross_amount = Decimal(str(incident["settlement_amount"]))
        attorney_fee_pct = Decimal(str(incident["attorney_fee_pct"]))
        lien_total = Decimal(str(incident["lien_total"] or 0))
        other_adjustments = Decimal(str(adjustments or 0))

        # Calculate attorney fee
        attorney_fee = (gross_amount * attorney_fee_pct / Decimal("100")).quantize(
            Decimal("0.01")
        )

        # Calculate net to client
        net_to_client = gross_amount - attorney_fee - lien_total - other_adjustments

        # Ensure we don't have negative values
        if net_to_client < 0:
            raise ValueError(
                f"Calculated negative net to client: {net_to_client}. "
                f"Please check settlement amount and deductions."
            )

        return {
            "gross": gross_amount,
            "attorney_fee": attorney_fee,
            "lien_total": lien_total,
            "other_adjustments": other_adjustments,
            "net_to_client": net_to_client,
        }

    except asyncpg.PostgresError as e:
        logger.error(
            f"Database error calculating split for incident {incident_id}: {e}",
            exc_info=True,
        )
        raise ValueError(f"Database error: {str(e)}") from e
    except Exception as e:
        logger.error(
            f"Error calculating split for incident {incident_id}: {e}",
            exc_info=True,
        )
        raise ValueError(f"Calculation error: {str(e)}") from e
    finally:
        if conn:
            await conn.close()

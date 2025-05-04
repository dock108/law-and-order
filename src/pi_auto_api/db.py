"""Database operations for the PI Automation API.

This module contains helpers for database operations.
"""

import json
import logging
from typing import Dict

import asyncpg

from pi_auto_api.config import settings
from pi_auto_api.schemas import IntakePayload

logger = logging.getLogger(__name__)


async def create_intake(payload: IntakePayload) -> Dict[str, int]:
    """Create a new client and incident record in the database.

    Args:
        payload: The intake payload containing client and incident data

    Returns:
        Dict containing the created client_id and incident_id

    Raises:
        Exception: If there's an error creating the records
    """
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set")

    try:
        # Connect to the database
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        try:
            # Start a transaction
            async with conn.transaction():
                # Insert client record
                client_query = """
                INSERT INTO client (full_name, dob, phone, email, address)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """
                client_id = await conn.fetchval(
                    client_query,
                    payload.client.full_name,
                    payload.client.dob,
                    payload.client.phone,
                    payload.client.email,
                    payload.client.address,
                )

                # Insert incident record
                incident_query = """
                INSERT INTO incident (
                    client_id, date, location, police_report_url,
                    injuries, vehicle_damage_text
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """
                incident_id = await conn.fetchval(
                    incident_query,
                    client_id,
                    payload.incident.date,
                    payload.incident.location,
                    (
                        str(payload.incident.police_report_url)
                        if payload.incident.police_report_url
                        else None
                    ),
                    json.dumps(payload.incident.injuries),
                    payload.incident.vehicle_damage_text,
                )

                # Return the IDs
                return {
                    "client_id": client_id,
                    "incident_id": incident_id,
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error creating intake: {str(e)}", exc_info=True)
        raise

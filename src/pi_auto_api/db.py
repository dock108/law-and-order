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

    conn = None
    try:
        # Connect to the database
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Start a transaction to ensure both inserts succeed or both fail
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
    except Exception as e:
        logger.error(f"Error creating intake: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure connection is closed even if an exception occurs
        if conn:
            await conn.close()


async def get_client_payload(client_id: int) -> dict:
    """Fetch client and incident data shaped for Docassemble retainer interview.

    Args:
        client_id: The ID of the client.

    Returns:
        A dictionary containing client and incident data.

    Raises:
        ValueError: If the client or incident is not found.
        Exception: If there is a database error.
    """
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set")

    conn = None
    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Use a transaction for consistent read
        async with conn.transaction():
            query = """
            SELECT
                c.full_name, c.dob, c.phone, c.email, c.address,
                i.date AS incident_date, i.location AS incident_location,
                i.injuries AS incident_injuries,
                i.vehicle_damage_text AS incident_vehicle_damage_text
            FROM client c
            JOIN incident i ON c.id = i.client_id
            WHERE c.id = $1;
            """
            record = await conn.fetchrow(query, client_id)

            if not record:
                raise ValueError(f"Client with ID {client_id} not found.")

            # Shape the data for Docassemble
            payload = {
                "client": {
                    "full_name": record["full_name"],
                    "dob": str(record["dob"]),  # Convert date to string
                    "phone": record["phone"],
                    "email": record["email"],
                    "address": record["address"],
                },
                "incident": {
                    "date": str(record["incident_date"]),  # Convert date to string
                    "location": record["incident_location"],
                    # Injuries are stored as JSON string, need to load them
                    "injuries": json.loads(record["incident_injuries"]),
                    "vehicle_damage_text": record["incident_vehicle_damage_text"],
                },
            }
            return payload
    except Exception as e:
        logger.error(f"Error fetching client data: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure connection is closed even if an exception occurs
        if conn:
            await conn.close()

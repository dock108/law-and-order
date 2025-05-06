"""Celery tasks for assembling and managing demand packages."""

import logging
from datetime import datetime
from typing import List, Optional

import asyncpg

from pi_auto_api.celery_app import app
from pi_auto_api.config import settings
from pi_auto_api.utils.package_rules import is_demand_ready
from pi_auto_api.utils.pdf_merge import merge_pdfs
from pi_auto_api.utils.storage import get_file_content, upload_file

logger = logging.getLogger(__name__)


@app.task(name="assemble_demand_package")
async def assemble_demand_package(incident_id: int) -> Optional[str]:
    """Assemble demand package for a given incident.

    Args:
        incident_id: The ID of the incident to build the demand package for.

    Returns:
        The ID of the newly created demand package document, or None if failed.
    """
    conn = None
    try:
        # Double-check the incident is ready for demand package
        if not await is_demand_ready(incident_id):
            logger.info(
                f"Incident {incident_id} is not ready for demand package assembly"
            )
            return None

        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Fetch all document IDs needed for the package
        query = """
        SELECT id, type FROM doc
        WHERE incident_id = $1
        AND type IN (
            'medical_records', 'medical_bill',
            'damages_worksheet_pdf', 'liability_photo'
        )
        ORDER BY
            CASE
                WHEN type = 'damages_worksheet_pdf' THEN 1
                WHEN type = 'liability_photo' THEN 2
                WHEN type = 'medical_records' THEN 3
                WHEN type = 'medical_bill' THEN 4
                ELSE 5
            END;
        """
        rows = await conn.fetch(query, incident_id)

        if not rows:
            logger.error(f"No documents found for incident {incident_id}")
            return None

        # Get the content of each document
        doc_contents: List[bytes] = []
        for row in rows:
            doc_id = row["id"]
            content = await get_file_content(doc_id)
            if content:
                doc_contents.append(content)
            else:
                logger.error(f"Could not retrieve content for document {doc_id}")

        if not doc_contents:
            logger.error(f"No contents for incident {incident_id} could be retrieved")
            return None

        # Merge all PDFs into one demand package
        merged_pdf = merge_pdfs(doc_contents)

        # Create new demand package document in the database
        insert_query = """
        INSERT INTO doc (incident_id, type, name, created_at)
        VALUES ($1, 'demand_package', $2, $3)
        RETURNING id;
        """

        timestamp = datetime.now().strftime("%Y-%m-%d")
        doc_name = f"Demand Package - {timestamp}"

        demand_package_id = await conn.fetchval(
            insert_query, incident_id, doc_name, datetime.now()
        )

        # Upload the merged PDF to storage
        upload_success = await upload_file(
            demand_package_id, merged_pdf, "application/pdf"
        )

        if not upload_success:
            logger.error(f"Failed to upload demand package for incident {incident_id}")
            # Delete the document record if upload failed
            await conn.execute("DELETE FROM doc WHERE id = $1", demand_package_id)
            return None

        logger.info(
            f"Demand package {demand_package_id} created for incident {incident_id}"
        )
        return demand_package_id

    except Exception as e:
        logger.error(
            f"Error assembling demand package for incident {incident_id}: {e}",
            exc_info=True,
        )
        return None
    finally:
        if conn:
            await conn.close()


@app.task(name="check_and_build_demand")
async def check_and_build_demand() -> int:
    """Check all incidents and build demand packages for eligible ones.

    This task runs nightly to check all incidents that don't have demand packages
    and builds packages for those that meet the criteria.

    Returns:
        Number of demand packages successfully created.
    """
    conn = None
    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Get all incident IDs without demand packages
        query = """
        SELECT DISTINCT i.id
        FROM incident i
        WHERE NOT EXISTS (
            SELECT 1 FROM doc d
            WHERE d.incident_id = i.id AND d.type = 'demand_package'
        );
        """

        incident_ids = [row["id"] for row in await conn.fetch(query)]

        if not incident_ids:
            logger.info("No incidents found that need demand packages")
            return 0

        logger.info(
            f"Checking {len(incident_ids)} incidents for demand package eligibility"
        )

        # Check each incident and build package if ready
        packages_created = 0
        for incident_id in incident_ids:
            if await is_demand_ready(incident_id):
                logger.info(f"Building demand package for incident {incident_id}")
                package_id = await assemble_demand_package(incident_id)
                if package_id:
                    packages_created += 1

        logger.info(f"Created {packages_created} demand packages in this run")
        return packages_created

    except Exception as e:
        logger.error(f"Error in check_and_build_demand task: {e}", exc_info=True)
        return 0
    finally:
        if conn:
            await conn.close()

"""Tasks for generating damages worksheets."""

import io
import logging

# from datetime import datetime
# Not strictly needed if only using for strftime in one place, can use pd.Timestamp
from typing import Any, Dict, List, Optional

import asyncpg
import pandas as pd

# import xlsxwriter # Handled by pandas engine
from weasyprint import HTML

from pi_auto_api.config import settings
from pi_auto_api.tasks import app
from pi_auto_api.utils.storage import upload_to_bucket

logger = logging.getLogger(__name__)


# Helper function to parse amount as a fallback
def _parse_amount_from_url(url: str, doc_id: int) -> Optional[float]:
    """Attempt to parse a monetary amount from a URL string."""
    try:
        filename_parts = url.split("_")
        for part in filename_parts:
            if "." in part:
                # Extract potential amount string, assuming format like xxx.xx
                potential_amount_str = part.split(".")[0] + "." + part.split(".")[1][:2]
                if all(c.isdigit() or c == "." for c in potential_amount_str):
                    amount = float(potential_amount_str)
                    logger.warning(
                        f"Parsed amount {amount} from URL for doc {doc_id} "
                        f"as DB amount was null."
                    )
                    return amount
    except Exception as e:
        logger.error(f"Error parsing amount from URL for doc {doc_id}: {e}")
    logger.warning(f"Could not parse amount for doc {doc_id}, using 0.0.")
    return 0.0


@app.task(name="build_damages_worksheet")
async def build_damages_worksheet(incident_id: int) -> Dict[str, Any]:
    """Builds Excel and PDF damages worksheets for an incident.

    - Queries all 'medical_bill' docs for the incident.
    - Sums amounts (from DB column `amount`, fallback to filename parsing if needed).
    - Uses pandas to build DataFrame: provider_name, bill_date (doc.created_at), amount.
    - Exports Excel (xlsxwriter) and styled PDF (pandas-to-html -> weasyprint).
    - Uploads both to Supabase bucket; inserts 'damages_worksheet' doc rows.
    - Returns totals dict.

    Args:
        incident_id: The ID of the incident.

    Returns:
        Dictionary with total damages, and URLs for Excel/PDF worksheets.
    """
    conn = None
    excel_url: Optional[str] = None
    pdf_url: Optional[str] = None
    total_damages: float = 0.0
    bills_data: List[Dict] = []

    logger.info(f"Building damages worksheet for incident_id: {incident_id}")

    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # 1. Query all 'medical_bill' docs for the incident
        # Join with provider table to get provider name
        query = """
        SELECT
            d.id AS doc_id,
            p.name AS provider_name,
            d.url AS bill_url,
            d.amount AS bill_amount,
            d.created_at AS bill_date
        FROM doc d
        JOIN provider p ON d.provider_id = p.id
        WHERE d.incident_id = $1 AND d.type = 'medical_bill'
        ORDER BY p.name, d.created_at;
        """
        bill_records = await conn.fetch(query, incident_id)

        if not bill_records:
            logger.info(
                f"No medical bills found for incident {incident_id}. Nothing to do."
            )
            return {
                "incident_id": incident_id,
                "status": "no_bills",
                "total_damages": 0.0,
                "excel_url": None,
                "pdf_url": None,
            }

        # 2. Prepare data and sum amounts
        for record in bill_records:
            amount = record["bill_amount"]
            if amount is None:
                amount = _parse_amount_from_url(record["bill_url"], record["doc_id"])

            bill_date_obj = record["bill_date"]
            bill_date_str = (
                bill_date_obj.strftime("%Y-%m-%d") if bill_date_obj else "N/A"
            )

            bills_data.append(
                {
                    "Provider": record["provider_name"],
                    "Date": bill_date_str,
                    "Amount": float(amount),  # Ensure it's float
                }
            )
            total_damages += float(amount)

        # 3. Use pandas to build DataFrame
        df = pd.DataFrame(bills_data)

        # 4. Export Excel (xlsxwriter) and styled PDF (pandas-to-html -> weasyprint)

        # --- Excel Export ---
        excel_io = io.BytesIO()
        with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Damages Worksheet", index=False)
            # Basic formatting (optional, can be expanded)
            workbook = writer.book
            worksheet = writer.sheets["Damages Worksheet"]
            header_format = workbook.add_format(
                {
                    "bold": True,
                    "text_wrap": True,
                    "valign": "top",
                    "fg_color": "#D7E4BC",
                    "border": 1,
                }
            )
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            # Auto-adjust column width (approximate)
            for i, col in enumerate(df.columns):
                # Calculate max length considering header and data
                column_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, column_len + 2)
        excel_bytes = excel_io.getvalue()

        # --- PDF Export ---
        # Basic HTML styling for the PDF
        html_string = f"""
        <html>
          <head><title>Damages Worksheet</title></head>
          <style>
            body {{ font-family: sans-serif; margin: 20px; }}
            h1 {{ text-align: center; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .total-row td {{ font-weight: bold; background-color: #e6e6e6; }}
          </style>
          <body>
            <h1>Damages Worksheet</h1>
            <h3>Incident ID: {incident_id}</h3>
            {df.to_html(index=False, classes='table table-striped')}
            <table class='table'>
                <tr class='total-row'>
                    <td><strong>Total Damages</strong></td>
                    <td colspan="2" style="text-align:right;">
                        <strong>${total_damages:,.2f}</strong>
                    </td>
                </tr>
            </table>
          </body>
        </html>
        """
        pdf_bytes = HTML(string=html_string).write_pdf()

        # 5. Upload both to Supabase bucket
        excel_url = await upload_to_bucket(
            excel_bytes
        )  # Filename will be generated by upload_to_bucket
        pdf_url = await upload_to_bucket(
            pdf_bytes
        )  # Filename will be generated by upload_to_bucket

        # Insert 'damages_worksheet' doc rows
        worksheet_doc_type = "damages_worksheet"
        insert_doc_query = """
        INSERT INTO doc (incident_id, type, url, status, created_at)
        VALUES ($1, $2, $3, 'generated', NOW()) RETURNING id;
        """
        excel_doc_type = f"{worksheet_doc_type}_excel"
        pdf_doc_type = f"{worksheet_doc_type}_pdf"
        await conn.execute(insert_doc_query, incident_id, excel_doc_type, excel_url)
        await conn.execute(insert_doc_query, incident_id, pdf_doc_type, pdf_url)

        logger.info(
            f"Damages worksheet generated and uploaded for incident {incident_id}"
        )

        return {
            "incident_id": incident_id,
            "status": "success",
            "total_damages": total_damages,
            "excel_url": excel_url,
            "pdf_url": pdf_url,
        }

    except Exception as e:
        logger.error(
            f"Error building damages worksheet for incident {incident_id}: {e}",
            exc_info=True,
        )
        return {
            "incident_id": incident_id,
            "status": "error",
            "error": str(e),
            "total_damages": total_damages,  # Could be partial
            "excel_url": excel_url,
            "pdf_url": pdf_url,
        }
    finally:
        if conn:
            await conn.close()

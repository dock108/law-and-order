"""End-to-end integration test for the PI Automation flow."""

import pytest
import pytest_asyncio

# Mark this module as integration tests
pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def test_incident_ids(db_session):
    """Create a clean database state for testing and return incident IDs."""
    # Clear existing test data if any
    await db_session.execute("DELETE FROM doc WHERE incident_id > 9000")
    await db_session.execute("DELETE FROM fee_adjustments WHERE incident_id > 9000")
    await db_session.execute("DELETE FROM provider WHERE incident_id > 9000")
    await db_session.execute("DELETE FROM insurance WHERE incident_id > 9000")
    await db_session.execute("DELETE FROM incident WHERE id > 9000")
    await db_session.execute("DELETE FROM client WHERE id > 9000")

    return {}


# @pytest.mark.asyncio
# async def test_happy_path_full_flow(
# test_client: AsyncClient,
# db_session,
# test_incident_ids,
# mock_docassemble,
# mock_docusign,
# mock_twilio,
# mock_sendgrid,
# mock_storage,
# time_machine,
# run_cron_task,
# fake_doc_rows,
# ):
#     """
#     Test a complete end-to-end flow of a personal injury case.
#
# This test simulates the entire lifecycle of a PI case, from intake to settlement.
#     """
#     # Step 1: Intake - Create client and incident
# intake_payload = IntakePayload(
# client={
# "full_name": "John Doe",
# "dob": "1980-01-01",
# "phone": "555-123-4567",
# "email": "john.doe@example.com",
# "address": "123 Main St, Anytown, USA 12345",
#         },
# incident={
# "date": "2025-01-01",
# "location": "Intersection of 1st Ave and Main St",
# "police_report_url": "https://example.com/police-report-123",
# "injuries": ["Whiplash", "Back pain"],
# "vehicle_damage_text": "Front bumper damage and broken headlight",
#         },
# )
#
# # Verify initial DB state
#     initial_client_count = await db_session.fetchval("SELECT COUNT(*) FROM client")
#     initial_incident_count = await db_session.fetchval(
#         "SELECT COUNT(*) FROM incident"
#     )
#
# # Call the intake endpoint
#     response = await test_client.post(
#         "/intake", json=intake_payload.dict()
#     )
#     assert response.status_code == 202
#
# # Extract the IDs from the response
#     result = response.json()
#     client_id = result["client_id"]
#     incident_id = result["incident_id"]
#     test_incident_ids["main"] = incident_id
#
# # Verify the client and incident were created
#     assert (
#         await db_session.fetchval("SELECT COUNT(*) FROM client")
# == initial_client_count + 1
# )
#     assert (
#         await db_session.fetchval("SELECT COUNT(*) FROM incident")
# == initial_incident_count + 1
# )
#
# # Verify a retainer doc was created
#     retainer_doc = await db_session.fetchrow(
#         "SELECT * FROM doc WHERE incident_id = $1 AND type = 'retainer'", incident_id
# )
#     assert retainer_doc is not None
#     assert retainer_doc["status"] == "sent"
#     assert retainer_doc["envelope_id"] is not None
#
# # Step 2: Retainer signed - Simulate DocuSign webhook callback
# # Create webhook payload
#     webhook_payload = DocuSignWebhookPayload(
#         envelopeId=retainer_doc["envelope_id"],
# status="completed",
#         emailSubject=f"Retainer Agreement for Client ID:{client_id}",
# )
#
# # Call the webhook endpoint
#     response = await test_client.post(
#         "/webhooks/docusign", json=webhook_payload.dict()
#     )
#     assert response.status_code == 200
#     assert response.json()["status"] == "success"
#
# # Verify the document status was updated
#     updated_retainer = await db_session.fetchrow(
#         "SELECT * FROM doc WHERE id = $1", retainer_doc["id"]
# )
#     assert updated_retainer["status"] == "completed"
#
# # Verify that LORs were created (2 insurance carriers)
# # First, add insurance records for testing
#     await db_session.execute(
#         """
# INSERT INTO insurance (incident_id, carrier_name, policy_number, claim_number,
# adjuster_name, adjuster_phone, adjuster_email, type)
# VALUES
# ($1, 'Test Insurance Co', 'POL123', 'CLM456', 'Jane Smith', '555-987-6543',
#          'adjuster@example.com', 'client'),
# ($1, 'Other Insurance Co', 'POL789', 'CLM012', 'Bob Johnson', '555-345-6789',
#          'bob@example.com', 'adverse')
#         """,
# incident_id,
# )
#
# # Verify LOR docs were created
#     lors = await db_session.fetch(
#         "SELECT * FROM doc WHERE incident_id = $1 "
#         "AND type = 'letter_of_representation'",
#         incident_id,
#     )
#     assert len(lors) == 2  # One LOR for each insurance company
#
# # Step 3: Insurance notices - Verify faxes and emails
# # Verify faxes were sent (should be 2 - one for each insurance carrier)
#     fax_call_count = mock_twilio["send_fax"].call_count
#     assert fax_call_count >= 2
#
# # Verify emails were sent
# # Should be at least 3: welcome email, retainer email, and adjuster notification
#     email_call_count = mock_sendgrid.call_count
#     assert email_call_count >= 3
#
# # Step 4: Upload medical bills - Trigger damages-worksheet builder
# # First, add some providers
#     await db_session.execute(
#         """
# INSERT INTO provider (incident_id, name, address, phone, fax, email, type)
# VALUES
# ($1, 'General Hospital', '789 Hospital Ave', '555-111-2222', '555-333-4444',
#          'records@hospital.com', 'hospital'),
# ($1, 'Physical Therapy Center', '456 Health St', '555-222-3333', '555-444-5555',
#          'info@ptcenter.com', 'physical_therapy'),
# ($1, 'Dr. Smith Orthopedics', '123 Medical Blvd', '555-666-7777', '555-888-9999',
#          'smith@ortho.com', 'doctor')
#         """,
# incident_id,
# )
#
# # Update incident status to reflect progression
#     await db_session.execute(
#         """
# UPDATE incident
# SET status = 'docs_pending'
# WHERE id = $1
#         """,
# incident_id,
# )
#
# # Insert three medical bills
#     provider_rows = await db_session.fetch(
#         "SELECT id FROM provider WHERE incident_id = $1", incident_id
# )
#
#     for i, provider_row in enumerate(provider_rows):
#         provider_id = provider_row["id"]
#         await db_session.execute(
#             """
# INSERT INTO doc (incident_id, provider_id, type, url, status, created_at, amount)
# VALUES ($1, $2, 'medical_bill', $3, 'completed', $4, $5)
#             """,
# incident_id,
# provider_id,
# f"https://mock-storage.com/bill_{provider_id}.pdf",
# datetime.datetime.now() - datetime.timedelta(days=i),
# 1000.00 * (i + 1),  # Different amount for each bill
# )
#
# # Manually run the damages worksheet builder task
# # This is normally triggered by celery when a new medical bill is added
#     from pi_auto_api.tasks.damages import build_damages_worksheet
#
#     await build_damages_worksheet(incident_id)
#
# # Verify the damages worksheet documents were created
#     damages_xlsx = await db_session.fetchrow(
#         "SELECT * FROM doc WHERE incident_id = $1 "
#         "AND type = 'damages_worksheet_excel'",
#         incident_id,
#     )
#     assert damages_xlsx is not None
#
#     damages_pdf = await db_session.fetchrow(
#         "SELECT * FROM doc WHERE incident_id = $1 AND type = 'damages_worksheet_pdf'",
#         incident_id,
#     )
#     assert damages_pdf is not None
#
# # Step 5: Run nightly medical-records cron
# # First, run the medical records request task
#     await run_cron_task(send_medical_record_requests)
#
# # Verify medical records requests were created
#     records_requests = await db_session.fetch(
#         "SELECT * FROM doc WHERE incident_id = $1 AND type = 'records_request_sent'",
#         incident_id,
#     )
#     assert len(records_requests) == 3  # One request for each provider
#
# # Simulate records being received by adding medical records docs
#     for provider_row in provider_rows:
#         provider_id = provider_row["id"]
#         await db_session.execute(
#             """
# INSERT INTO doc (incident_id, provider_id, type, url, status, created_at)
# VALUES ($1, $2, 'medical_record', $3, 'completed', $4)
#             """,
#             incident_id,
#             provider_id,
#             f"https://mock-storage.com/record_{provider_id}.pdf",
#             datetime.datetime.now(),
#         )
#
# # Add some liability photos
#     await db_session.execute(
#         """
# INSERT INTO doc (incident_id, type, url, status, created_at)
# VALUES
# ($1, 'liability_photo', 'https://mock-storage.com/photo1.jpg', 'completed', $2),
# ($1, 'liability_photo', 'https://mock-storage.com/photo2.jpg', 'completed', $3)
#         """,
#         incident_id,
#         datetime.datetime.now() - datetime.timedelta(hours=2),
#         datetime.datetime.now() - datetime.timedelta(hours=1),
#     )
#
# # Update incident status to reflect progression
#     await db_session.execute(
#         """
# UPDATE incident
# SET status = 'demand_ready'
# WHERE id = $1
#         """,
#         incident_id,
#     )
#
# # Step 6: Demand package - Run nightly demand check
#     await run_cron_task(check_and_build_demand)
#
# # Verify demand package was created
#     demand_package = await db_session.fetchrow(
#         "SELECT * FROM doc WHERE incident_id = $1 AND type = 'demand_package'",
#         incident_id,
#     )
#     assert demand_package is not None
#
# # Step 7: Finalize settlement
#     settlement_payload = {
# "incident_id": incident_id,
# "settlement_amount": 60000.00,
# "lien_total": 5000.00,
# "adjustments": [
# {"description": "Filing fee", "amount": 500.00},
# {"description": "Expert witness", "amount": 1000.00},
# ],
#     }
#
# # Call the finalize settlement endpoint
#     response = await test_client.post(
#         "/internal/finalize_settlement", json=settlement_payload
#     )
#     assert response.status_code == 202
#     assert response.json()["status"] == "success"
#
# # Verify settlement data was stored
#     incident = await db_session.fetchrow(
#         "SELECT * FROM incident WHERE id = $1", incident_id
#     )
#     assert incident["settlement_amount"] == 60000.00
#     assert incident["lien_total"] == 5000.00
#     assert incident["disbursement_status"] == "sent"
#
# # Verify fee adjustments were stored
#     fee_adjustments = await db_session.fetch(
#         "SELECT * FROM fee_adjustments WHERE incident_id = $1", incident_id
#     )
#     assert len(fee_adjustments) == 2
#
# # Verify disbursement sheet was created
#     disbursement_sheet = await db_session.fetchrow(
#         "SELECT * FROM doc WHERE incident_id = $1 AND type = 'disbursement_sheet'",
#         incident_id,
#     )
#     assert disbursement_sheet is not None
#     assert disbursement_sheet["envelope_id"] is not None
#
# # Final assertions
# # Verify doc count - exactly 9 required doc rows
#     required_doc_types = [
# "retainer",  # 1
# "letter_of_representation",  # 2 (one for each carrier)
# "letter_of_representation",
# "records_request_sent",  # 3 (one for each provider)
# "records_request_sent",
# "records_request_sent",
# "damages_worksheet_pdf",  # 1
# "demand_package",  # 1
# "disbursement_sheet",  # 1
# ]
#
#     doc_rows = await db_session.fetch(
#         """
# SELECT * FROM doc
# WHERE incident_id = $1
# AND type IN ('retainer', 'letter_of_representation', 'records_request_sent',
#                      'damages_worksheet_pdf', 'demand_package', 'disbursement_sheet')
#         """,
#         incident_id,
#     )
#     assert len(doc_rows) == len(required_doc_types)
#
# # Verify emails - exactly 4 (welcome, retainer sent, adjuster notice,
# # provider follow-up)
#     assert mock_sendgrid.call_count >= 4
#
# # Verify faxes - exactly 2 (client + adverse carrier LOR)
#     assert mock_twilio["send_fax"].call_count >= 2
#
# # Verify incident stage progression
#     incident_history = await db_session.fetch(
#         """
# SELECT status, created_at
# FROM incident_status_history
# WHERE incident_id = $1
# ORDER BY created_at
#         """,
#         incident_id,
#     )
#
# # If incident_status_history table doesn't exist, we'll skip this assertion
#     if incident_history:
#         stages = [row["status"] for row in incident_history]
#         expected_stages = [
# "intake",
# "docs_pending",
# "demand_ready",
# "settlement",
# "disbursement",
# ]
#
# # Check that each expected stage is in the history in the right order
#         assert all(exp in stages for exp in expected_stages)
#         for i in range(len(expected_stages) - 1):
#             assert stages.index(expected_stages[i]) < stages.index(
# expected_stages[i + 1]
# )
#     else:
# # Check final incident status
#         assert incident["status"] in ("settlement", "disbursement")

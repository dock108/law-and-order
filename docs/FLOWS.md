# Process Flows

This document outlines the key process flows in the PI Automation system.

## Client Intake and Retainer Generation

The following sequence diagram shows the flow of data from the client intake API
through Celery for asynchronous processing, Docassemble for document generation,
and DocuSign for e-signature.

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DB as Supabase
    participant Queue as Celery+Redis
    participant Worker as Celery Worker
    participant DA as Docassemble
    participant DS as DocuSign
    participant TW as Twilio

    Client->>API: POST /intake
    API->>DB: Create client & incident
    API->>Queue: Enqueue generate_retainer task
    API-->>Client: Return intake_id 202 Accepted

    Note over Worker: Asynchronous processing
    Queue->>Worker: Process generate_retainer task
    Worker->>DB: Fetch client & incident data (get_client_payload)
    Worker->>DA: Call /api/v1/generate/retainer (generate_retainer_pdf)
    DA-->>Worker: Return PDF document bytes
    Worker->>DS: Send envelope for e-signature (send_envelope)
    DS-->>Client: Email with signing link
    Worker->>TW: Send SMS confirmation (send_sms)
    TW-->>Client: SMS notification about retainer
    Worker->>DB: Update task status (TODO)

```

## DocuSign Webhook and Insurance Notice Flow

The following sequence diagram shows the flow after a client signs a retainer agreement,
triggering the automatic generation and delivery of Letters of Representation (LOR) to insurance carriers.

```mermaid
sequenceDiagram
    participant Client
    participant DS as DocuSign
    participant API as FastAPI
    participant Queue as Celery+Redis
    participant Worker as Celery Worker
    participant DA as Docassemble
    participant DB as Supabase
    participant TW as Twilio
    participant Mail as SendGrid

    Client->>DS: Signs retainer agreement
    DS->>API: POST /webhooks/docusign (envelope completed)
    API->>Queue: Enqueue send_insurance_notice task
    API-->>DS: 200 OK (webhook acknowledged)

    Note over Worker: Asynchronous processing
    Queue->>Worker: Process send_insurance_notice task
    Worker->>DB: Fetch client & insurance data (get_insurance_payload)
    Worker->>DA: Call /api/v1/generate/letters/lor
    DA-->>Worker: Return LOR PDF document bytes

    Note over Worker: Send to client's insurer
    Worker->>TW: Send fax to client's insurance (send_fax)

    Note over Worker: Send to adverse carriers
    Worker->>TW: Send fax to adverse insurance (send_fax)
    Worker->>Mail: Email to adjuster with notification (send_mail)

    Worker->>DB: Update task status
```

## Nightly Medical-Records Request Flow

The following diagram shows the automated nightly process for sending medical record requests to healthcare providers who haven't sent records yet.

```mermaid
sequenceDiagram
    participant CB as Celery Beat
    participant Worker as Celery Worker
    participant DB as Supabase
    participant DA as Docassemble
    participant Storage as Supabase Storage
    participant TW as Twilio
    participant Provider

    Note over CB: 2:00 AM ET Daily
    CB->>Worker: Trigger send_medical_record_requests task
    Worker->>DB: Query for providers needing records

    loop For each pending provider
        Worker->>DB: Get provider payload data
        Worker->>DA: Generate medical records request letter
        DA-->>Worker: Return PDF document bytes
        Worker->>Storage: Upload PDF (upload_to_bucket)
        Storage-->>Worker: Return signed URL (24h)
        Worker->>TW: Send fax to provider (send_fax)
        Worker->>DB: Log request in documents table
    end

    Note over Provider: Later...
    Provider->>DB: Medical records received and logged
```

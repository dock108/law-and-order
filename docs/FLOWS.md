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
    Worker->>DB: Update task status (TODO)

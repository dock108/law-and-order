# Process Flows

This document outlines the key process flows in the PI Automation system.

## Client Intake and Retainer Generation

The following sequence diagram shows the flow of data from the client intake API
through Celery for asynchronous processing to Docassemble for document generation.

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
    Worker->>DB: Fetch client & incident data
    Worker->>DA: Call /api/v1/generate/retainer
    DA-->>Worker: Return PDF document
    Worker->>DS: Send for e-signature
    Worker->>DB: Update task status

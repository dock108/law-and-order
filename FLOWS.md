## Automated Demand Package Assembly (Planned)

This flow will describe the process of automatically assembling a demand package once all necessary documents for an incident are available.

1.  **Trigger**: A nightly scheduled job (Celery Beat) will periodically scan incidents.
2.  **Condition Check**: For each relevant incident, a utility function (`utils.package_rules.is_demand_ready`) checks if all prerequisites for a demand package are met:
    *   Existence of medical records document(s).
    *   Existence of a generated damages worksheet (PDF).
    *   Existence of all associated provider medical bills.
    *   Existence of at least one liability photo.
    *   Absence of an existing `demand_package` document for the incident.
3.  **Task Queuing**: If an incident is ready, the `assemble_demand_package` Celery task is queued for that incident.
4.  **Package Assembly (`assemble_demand_package` task):
    *   **Fetch Data**: Gather necessary data for the incident (client details, incident specifics, damages totals from the worksheet).
    *   **Generate Demand Letter**: Call an external service (e.g., Docassemble via `externals.docassemble.generate_letter`) to create the main demand letter PDF using the fetched data.
    *   **Collect Exhibits**: Retrieve the PDF versions of:
        *   Damages Worksheet.
        *   Consolidated Medical Records.
        *   Liability Photos (converted to PDF pages if necessary).
        *   (Potentially other documents like policy information - TBD).
    *   **Merge PDFs**: Use a utility (`utils.pdf_merge.merge_pdfs`) to combine the generated demand letter and all exhibit PDFs into a single `demand_package.pdf`.
    *   **Upload & Record**: Upload the merged PDF to the cloud storage bucket and create a new `doc` table entry with `type = 'demand_package'` and the URL of the uploaded file.
5.  **Outcome**: A complete demand package PDF is stored and linked to the incident.

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant Scheduler as Nightly Job
    participant Rules as is_demand_ready()
    participant Queue as Celery Queue
    participant Task as assemble_demand_package()
    participant DB as Database
    participant Docassemble
    participant Storage

    Beat->>Scheduler: Trigger nightly check
    Scheduler->>DB: Fetch incidents
    loop For each incident
        Scheduler->>Rules: Check readiness(incident_id)
        Rules->>DB: Query doc table (records, worksheet, bills, photos)
        Rules-->>Scheduler: Boolean (is_ready)
        alt is_ready = true AND no existing package
            Scheduler->>Queue: Enqueue assemble_demand_package(incident_id)
        end
    end

    Queue-->>Task: Process task(incident_id)
    Task->>DB: Fetch incident data, damages totals
    Task->>Docassemble: generate_letter('demand', payload)
    Docassemble-->>Task: demand_letter.pdf (bytes)
    Task->>DB: Fetch exhibit URLs (worksheet, records, photos)
    Task->>Storage: Fetch exhibit PDF bytes (if not already local)
    Note over Task, Storage: Convert photo images to PDF pages
    Task->>Task: merge_pdfs([letter_bytes, exhibit1_bytes, ...])
    Task-->>Storage: Upload merged_demand_package.pdf
    Storage-->>Task: URL of merged PDF
    Task->>DB: Insert doc row (type='demand_package', url)
```

## Document Processing (Medical Bill Example)

# Personal Injury Automation

[![Backend CI](https://github.com/law-and-order/pi-auto/actions/workflows/backend.yml/badge.svg)](https://github.com/law-and-order/pi-auto/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/law-and-order/pi-auto/actions/workflows/frontend.yml/badge.svg)](https://github.com/law-and-order/pi-auto/actions/workflows/frontend.yml)
[![Contract Tests](https://github.com/law-and-order/pi-auto/actions/workflows/contract-tests.yml/badge.svg)](https://github.com/law-and-order/pi-auto/actions/workflows/contract-tests.yml)

<!--
API docs badge only displays in production environments to avoid 404 errors in preview environments
[![API Docs](https://img.shields.io/badge/API-Docs-blue)](https://github.com/law-and-order/pi-auto/actions)
-->

A comprehensive set of tools for automating personal injury case management and workflows.

👉 **New here? See the [Developer Getting Started Guide](docs/DEVELOPMENT.md)**

## Requirements

- Python 3.11+
- Poetry
- pnpm (for frontend development)

## Directory Structure

```
pi-auto/
├── apps/
│   └── web/        # Next.js 14 frontend application
├── packages/
│   ├── api-client/ # TypeScript SDK for the backend API
│   └── ui/         # Shared React component library (e.g., Button, Form elements)
├── src/
│   └── pi_auto_api/  # FastAPI backend application
├── tests/            # Python backend tests
├── templates/        # Jinja templates for document generation
├── openapi/          # OpenAPI specifications
├── scripts/          # Utility scripts
├── .github/workflows # GitHub Actions CI/CD workflows
├── Dockerfile        # Docker configuration for the backend
├── poetry.lock
├── pyproject.toml
├── pnpm-lock.yaml
├── package.json      # Root pnpm workspace config
└── README.md
```

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/your-org/pi-auto.git
cd pi-auto
```

2. Install all dependencies (Python backend and Node.js frontend):

```bash
poetry install # Installs Python dependencies
pnpm install   # Installs Node.js dependencies for all workspaces
```

3. Activate the Python virtual environment:

```bash
poetry shell
```

4. Run the development servers:

   Start the Next.js frontend (in a new terminal window/tab):

   ```bash
   pnpm -C apps/web dev
   ```

   Start the FastAPI backend API (in a new terminal window/tab, after `poetry shell`):

   ```bash
   poetry run uvicorn pi_auto_api.main:app --reload
   ```

5. Run tests:

   Run Python backend tests:

   ```bash
   pytest
   ```

   Run Frontend tests (in a new terminal window/tab):

   ```bash
   pnpm -C apps/web test
   ```

## API

### API spec

The PI Workflow API is defined by an OpenAPI 3.1 specification.

- View the [OpenAPI spec file](openapi/pi-workflow.yaml).
- You can test the stubbed `/api/cases` endpoint (once the API is running locally) with:
  ```bash
  curl http://localhost:9000/api/cases
  ```

### API Client SDK

A TypeScript SDK is automatically generated from the OpenAPI spec. It can be found in the `packages/api-client` directory within this monorepo.

Install it in another package within the monorepo:

```bash
pnpm add @pi-monorepo/api-client --workspace <your-package-name>
```

Example Usage:

```typescript
import createClient from '@pi-monorepo/api-client';

// Assuming your API is running at http://localhost:9000
const client = createClient({ baseUrl: 'http://localhost:9000' });

async function fetchCases() {
  const { data, error } = await client.GET('/api/cases');

  if (error) {
    console.error('Error fetching cases:', error);
    return;
  }

  if (data) {
    console.log('Cases:', data);
    // Process the cases (data will be typed according to the OpenAPI spec)
  }
}

fetchCases();
```

CI automatically checks for drift between the OpenAPI spec and the generated client.

### Run the API locally

The PI Automation API provides a RESTful interface for managing personal injury cases.

1. Set up environment variables (create a `.env` file in the project root):

```bash
SUPABASE_URL=postgresql://user:password@localhost:5432/dbname
SUPABASE_KEY=your-supabase-key
DOCASSEMBLE_URL=http://localhost:5000
ALLOWED_ORIGINS=http://localhost:3000
```

2. Start the API server:

```bash
poetry run uvicorn pi_auto_api.main:app --reload
```

3. Access the API documentation at http://localhost:8000/docs

### CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured via the `ALLOWED_ORIGINS` environment variable. Provide a comma-separated list of allowed origins. Example for local development and a production frontend:

```bash
ALLOWED_ORIGINS=http://localhost:3000,https://app.yourdomain.com
```

4. Health endpoints:

   - `/healthz` - Simple health check
   - `/readyz` - Deep health check (database and Docassemble connectivity)

5. Client Intake endpoint:
   ```bash
   curl -X POST http://localhost:8000/intake \
     -H "Content-Type: application/json" \
     -d '{
       "client": {
         "full_name": "John Doe",
         "dob": "1980-01-01",
         "phone": "555-123-4567",
         "email": "john.doe@example.com",
         "address": "123 Main St, Anytown, USA 12345"
       },
       "incident": {
         "date": "2023-05-15",
         "location": "Intersection of 1st Ave and Main St",
         "police_report_url": "https://example.com/police-report-123",
         "injuries": ["Whiplash", "Back pain"],
         "vehicle_damage_text": "Front bumper damage and broken headlight"
       }
     }'
   ```

### Staff Authentication

Staff members (paralegals, lawyers) can authenticate to the API using a JWT-based login flow.

**1. Login Endpoint:**

To obtain an access token, `POST` to the `/auth/login` endpoint with the staff member's email and password:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "staff.member@example.com",
    "password": "yoursecurepassword"
  }'
```

**Response (Success - 200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response (Failure - 401 Unauthorized):**

```json
{
  "detail": "Incorrect email or password"
}
```

**2. Accessing Protected Routes:**

Once authenticated, include the `access_token` in the `Authorization` header as a Bearer token for requests to protected API endpoints:

```bash
curl -X GET http://localhost:8000/api/cases \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

If the token is missing, expired, or invalid, the API will respond with a `401 Unauthorized` error.

### Live Activity Feed

The API provides a Server-Sent Events (SSE) stream at `/api/events/stream` to receive live updates about activities within the system, such as task completions or document status changes. Clients can subscribe to this stream to provide real-time feedback in a user interface.

**Subscribing to the Event Stream (Browser Example):**

```javascript
const eventSource = new EventSource('http://localhost:8000/api/events/stream'); // Replace with your API URL

eventSource.onopen = function () {
  console.log('Connection to SSE stream opened.');
};

eventSource.onmessage = function (event) {
  console.log('New event received:');
  console.log('  ID:', event.lastEventId); // The ID is a millisecond timestamp
  try {
    const eventData = JSON.parse(event.data);
    console.log('  Data:', eventData);
    // Process the eventData object (e.g., update UI)
    // Example: if (eventData.type === 'disbursement_sent') { ... }
  } catch (e) {
    console.error('Error parsing event data:', e);
  }
};

// Optional: Handle custom named events if the server sends them
// eventSource.addEventListener('custom_event_name', function(event) {
//   console.log("Custom event:", event.data);
// });

eventSource.onerror = function (err) {
  if (eventSource.readyState === EventSource.CLOSED) {
    console.log('Connection to SSE stream closed.');
  }
  console.error('Error with SSE stream:', err);
  // Optionally, attempt to reconnect here
};

// To close the connection from the client side:
// eventSource.close();
```

**Event Format:**

Events are streamed in the following format:

```
id:<timestamp_ms>
data:{"type":"event_type","key":"value",...}

```

A keep-alive comment (`: keep-alive`) is sent every 30 seconds to prevent connection timeouts.

The `Last-Event-ID` header can be sent by the client on reconnect to request events since the last received ID, though this is currently ignored by the server (v1).

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
        DA-->>Worker: Return PDF bytes
        Worker->>Storage: Upload PDF, get signed URL
        Storage-->>Worker: Return signed URL
        Worker->>TW: Queue fax with signed URL
        TW-->>Worker: Return fax SID
        Worker->>DB: Insert 'records_request_sent' doc row (URL, SID)
    end

    Worker-->>CB: Task complete
```

### Damages Worksheet Generation

When a new medical bill document is added to the system (e.g., via the `process_medical_bill` task), a task is queued to automatically generate and update a damages worksheet for the associated incident. This worksheet is created in both Excel (.xlsx) and PDF formats.

1.  **Trigger**: The `process_medical_bill` task, after successfully adding a `medical_bill` document row to the database, queues the `build_damages_worksheet` task for the relevant `incident_id`.
2.  **Data Aggregation**: The `build_damages_worksheet` task queries all `medical_bill` document rows for the specified incident.
3.  **Calculation**: It sums the `amount` listed for each bill. If the `amount` is missing in the database, it attempts a fallback to parse the amount from the document's URL/filename (this parsing is currently basic).
4.  **Report Generation**: Using the aggregated data, it generates:
    - An **Excel file** (.xlsx) listing each provider, bill date, and amount, along with the total damages, using `pandas` and `xlsxwriter`.
    - A **PDF file** with similar information, styled for readability using `pandas` HTML export and `WeasyPrint`.
5.  **Storage**: Both the Excel and PDF files are uploaded to the Supabase storage bucket.
6.  **Database Update**: Two new document rows are inserted into the `doc` table for the incident:
    - One with `type = 'damages_worksheet_excel'` and the URL of the uploaded Excel file.
    - One with `type = 'damages_worksheet_pdf'` and the URL of the uploaded PDF file.

_(Placeholder for a screenshot of the generated damages worksheet)_

### Automated Damages Worksheets

When new medical bills are logged, the system automatically generates and stores Excel (.xlsx) and PDF (.pdf) damages worksheets. These worksheets summarize all medical bills for an incident, calculate total damages, and are uploaded to cloud storage. This feature is triggered by the `process_medical_bill` task which in turn calls `build_damages_worksheet`.

### Automated Demand Package Assembly

The system automatically assembles demand packages when all required documents for an incident are present. This process runs nightly, checking eligible incidents and creating merged PDF packages.

1. **Document Requirements**: A demand package requires:

   - Medical records for the incident
   - At least one medical bill for each provider associated with the incident
   - Damages worksheet PDF
   - Liability photos
   - No existing demand package for the incident

2. **Package Assembly Process**:

   ```mermaid
   sequenceDiagram
       participant CB as Celery Beat
       participant Worker as Celery Worker
       participant DB as Supabase
       participant Storage as Supabase Storage

       Note over CB: 3:00 AM ET Daily
       CB->>Worker: Trigger check_and_build_demand task
       Worker->>DB: Query for incidents without demand packages

       loop For each incident
           Worker->>DB: Check if incident meets criteria
           alt All requirements met
               Worker->>DB: Fetch all required documents
               Worker->>Storage: Get document content for each doc
               Worker->>Worker: Merge PDFs into single document
               Worker->>DB: Create demand_package doc record
               Worker->>Storage: Upload merged PDF
               Worker->>DB: Update with file URL
           end
       end

       Worker-->>CB: Task complete
   ```

3. **On-Demand Assembly**: The demand package can also be manually triggered for a specific incident via the API:

   ```bash
   curl -X POST http://localhost:8000/demand/create/{incident_id}
   ```

4. **Document Order**: Documents in the merged PDF follow a specific order:
   - Damages worksheet (summary of costs)
   - Liability photos
   - Medical records
   - Medical bills

### Disbursement Sheet Generator & E-Sign

After a settlement is finalized, the system automatically calculates fee and lien splits, generates a disbursement sheet, and sends it to the client for signature through DocuSign.

1. **Settlement Finalization Process**:

   ```mermaid
   sequenceDiagram
       participant API as API Endpoint
       participant DB as Supabase
       participant Worker as Celery Worker
       participant DA as Docassemble
       participant DS as DocuSign
       participant Client

       API->>DB: Update incident settlement data
       API->>DB: Store fee adjustments (if any)
       API->>Worker: Queue generate_disbursement_sheet task
       Worker->>DB: Fetch incident and client details
       Worker->>Worker: Calculate settlement split
       Worker->>DA: Generate disbursement sheet PDF
       DA-->>Worker: Return PDF bytes
       Worker->>DS: Send PDF for e-signature
       DS-->>Worker: Return envelope ID
       Worker->>DB: Update disbursement_status to 'sent'
       Worker->>DB: Insert 'disbursement_sheet' doc row
       DS->>Client: Send e-signature request
       Client->>DS: Sign document
       DS->>API: Webhook notification (signed)
       API->>DB: Update disbursement_status to 'signed'
   ```

2. **Calculation Logic**: The disbursement calculator computes the settlement split:

   - Gross settlement amount
   - Attorney fee (based on percentage)
   - Medical liens
   - Other adjustments/deductions
   - Net amount to client

3. **Settlement Finalization Endpoint**:

   ```bash
   curl -X POST http://localhost:8000/internal/finalize_settlement \
     -H "Content-Type: application/json" \
     -d '{
       "incident_id": 123,
       "settlement_amount": 60000,
       "lien_total": 5000,
       "adjustments": [
         {"description": "Filing fee", "amount": 500},
         {"description": "Expert witness", "amount": 1000}
       ]
     }'
   ```

4. **Disbursement Sheet Example**:
   - Clearly shows all components of the settlement
   - Includes signature blocks for client and attorney
   - Sent via DocuSign for secure e-signature
   - Status tracked in the database (`pending`, `sent`, `signed`)

## Development

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. Install them with:

```bash
poetry run pre-commit install
```

To run all pre-commit hooks manually:

```bash
poetry run pre-commit run --all-files
```

### Code Style

This project uses:

- [Black](https://github.com/psf/black) for code formatting
- [isort](https://github.com/PyCQA/isort) for import sorting
- [ruff](https://github.com/charliermarsh/ruff) for linting

### Conventional Commits

The project follows [Conventional Commits](https://www.conventionalcommits.org/), which are enforced via pre-commit hooks:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types include: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

## Templates

Legal document templates are stored in the `templates/` directory, organized by purpose:

- `templates/intake/` - Client intake forms and agreements
- `templates/correspondence/` - Letters and communications
- `templates/medical/` - Medical record requests and authorizations
- `templates/settlement/` - Demand letters and settlement documents
- `templates/workflow/` - Task lists and internal workflow documents

All templates use Jinja-style tags (e.g., `{{ client.full_name }}`) for dynamic content. See `docs/TEMPLATE_REFERENCE.md` for a complete list of available tags.

### Checking Templates for PII

To verify that templates do not contain any personally identifiable information (PII):

```bash
python scripts/check_templates.py
```

### Template Guard (CI)

A dedicated CI job automatically checks templates for potential issues before code can be merged into `main`.
This helps prevent accidental PII leaks and ensures template consistency.

The guard fails if any file in `templates/` or `email_templates/` contains:

- **Potential PII**: Hard-coded names (e.g., `John Doe`), phone numbers (e.g., `555-123-4567`), specific date formats (e.g., `01/01/2024`), or SSNs (e.g., `123-45-6789`).
- **Unwrapped Dollar Amounts**: Currency values like `$100.00` that are not enclosed within Jinja tags (e.g., `{{ amount }}`).
- **Empty Merge Fields**: Placeholders like `{{ }}` or `{{}}` (with optional whitespace).
- **Undefined Jinja Tags**: Any tag like `{{ client.non_existent_field }}` that is not defined in `docs/TEMPLATE_REFERENCE.md`.

To run the guard locally:

```bash
poetry run pytest -m template_guard
```

If the guard fails, it will print the file path, line number, violation type, and the problematic text. Update the template or the `docs/TEMPLATE_REFERENCE.md` file as needed to resolve the issue.

## Database

This project uses PostgreSQL with Supabase for data storage. The database schema includes the following tables:

- `client` - Client personal information
- `incident` - Accident/incident details
- `insurance` - Insurance policy information
- `provider` - Medical provider information
- `doc` - Document storage and tracking
- `task` - Case workflow and task management

### Row-Level Security

Row-Level Security policies are implemented for all tables to ensure proper data access control:

- Lawyers and paralegals have access to all records
- Clients can only access their own records
- Tasks can be accessed by assignees even if they can't access the full case

### Migrations

Database migrations are managed with Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Revert to a previous migration
alembic downgrade <revision_id>
```

## License

Proprietary - All Rights Reserved

## Testing

Tests are written using `pytest` and located in the `tests/` directory.

To run tests locally:

1.  Ensure you have a testing database configured (e.g., using Docker or a local PostgreSQL instance). See "RLS Testing" in `docs/SCHEMA.md` for CI setup which can be adapted locally.
2.  Set the `TEST_DATABASE_URL` environment variable if not using the default expected by `tests/conftest.py` (`postgresql+asyncpg://testuser:testpassword@localhost:5432/testdb`).
3.  Run migrations: `poetry run alembic upgrade head` (ensure `SUPABASE_URL` is set for Alembic).
4.  Seed the test database: `psql $TEST_DATABASE_URL -f seed.sql` (adjust command based on your `psql` access).
5.  Run pytest, including coverage reporting:

```bash
poetry run pytest --cov=src/pi_auto
```

Tests are automatically run in CI on every push and pull request to the `main` branch, including coverage checks enforced at >= 80%.

## Docassemble Integration

### Run Docassemble locally

To set up and run the Docassemble document automation server locally:

1. Make sure Docker and Docker Compose are installed on your system.

2. Start the Docassemble containers:

```bash
cd docker/docassemble
docker compose up -d
```

3. Check if Docassemble is running properly:

```bash
poetry run python scripts/health_docassemble.py
```

4. Once running, you can access the Docassemble web interface at http://localhost:8100.

5. To stop the containers:

```bash
cd docker/docassemble
docker compose down
```

The `templates/` directory is mounted inside the Docassemble container at `/usr/share/docassemble/files/templates`, making all your templates available for use in interviews and document generation.

## Running Celery

The API uses Celery with Redis for background task processing.

### Start the Redis and Celery worker

Using docker-compose:

```bash
docker compose up redis celery_worker
```

Or run just the Celery worker:

```bash
poetry run celery -A pi_auto_api.tasks worker --loglevel=INFO
```

Background tasks like generating retainer agreements and sending them for e-signature are handled asynchronously by Celery workers.

### Task Types

- `generate_retainer`: Generates a retainer agreement for a client and submits it for e-signature

### Automated Retainer Flow

The primary background task is generating and sending the retainer agreement after client intake.

```mermaid
graph LR
    A[Client Submits Intake via API] --> B(API Creates DB Records);
    B --> C{Enqueue generate_retainer Task};
    C --> D[Celery Worker Picks Up Task];
    D --> E(Worker Fetches Client/Incident Data from DB);
    E --> F(Worker Calls Docassemble API);
    F --> G{Docassemble Generates PDF};
    G --> H(Worker Calls DocuSign API);
    H --> I{DocuSign Sends Email for Signature};
    I --> J(Worker Updates Task Status);
```

## Email Adapter

The application includes an email adapter for sending templated emails via SendGrid.

### Configuration

1. Set up your SendGrid API key in the `.env` file:

```bash
SENDGRID_API_KEY=your_sendgrid_api_key
```

### Email Templates

Email templates are located in the `src/pi_auto_api/email_templates/` directory and use Jinja2 syntax for dynamic content:

- `welcome.html` - Welcome email for new clients
- `retainer_sent.html` - Notification that a retainer has been sent for signature

### Sending Emails

To send an email from your code:

```python
from pi_auto_api.externals.sendgrid_client import send_mail

# Example: Send welcome email
await send_mail(
    template_name="welcome.html",
    to_email="client@example.com",
    template_ctx={
        "client": {
            "full_name": "John Doe",
            "email": "client@example.com"
        },
        "support_email": "support@example.com",
        "support_phone": "555-123-4567"
    }
)
```

For a complete list of available email templates and context variables, see the [Template Reference](docs/TEMPLATE_REFERENCE.md).

## SMS & Fax Adapter

The application includes a Twilio adapter for sending SMS messages and faxes.

### Configuration

1. Set up your Twilio credentials in the `.env` file:

```bash
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_SMS_FROM=+15551234567
TWILIO_FAX_FROM=+15551234567
```

### Sending SMS Messages

To send an SMS notification to a client:

```python
from pi_auto_api.externals.twilio_client import send_sms

# Example: Send confirmation SMS
await send_sms(
    to="+15557654321",
    body="Your retainer agreement has been sent. Please check your email to sign it."
)
```

### Sending Faxes

To send a fax to an insurance company or medical provider:

```python
from pi_auto_api.externals.twilio_client import send_fax

# Example: Send letter of representation
await send_fax(
    to="+15557654321",
    media_url="https://example.com/documents/letter_of_representation.pdf"
)
```

### Retry Logic

Both SMS and fax operations include built-in exponential backoff retry logic for transient errors (HTTP 5xx and 429):

- Maximum 3 attempts
- Exponential backoff starting at 1 second, doubling after each failure
- Non-transient errors (HTTP 4xx except 429) are not retried

## Insurance Notice Flow

The application includes automated Letter of Representation (LOR) generation and distribution to insurance carriers when a client signs their retainer agreement.

```mermaid
flowchart TD
    A[Client Signs Retainer Agreement] --> B[DocuSign Webhook Notification]
    B --> C[Send Insurance Notice Task Queued]
    C --> D[Fetch Client & Insurance Data]
    D --> E[Generate LOR PDF via Docassemble]
    E --> F[Send Faxes to Insurance Carriers]
    E --> G[Send Emails to Insurance Adjusters]
```

The automated insurance notice process:

1. Client signs the retainer agreement via DocuSign
2. DocuSign sends a webhook notification to our API
3. Our system verifies the webhook and enqueues a background task
4. The task retrieves client and insurance information from the database
5. Docassemble generates a Letter of Representation PDF
6. The system sends faxes to all relevant insurance carriers via Twilio
7. If adjuster emails are available, notification emails are also sent via SendGrid

This automation eliminates manual steps and ensures timely notice to all insurance carriers as soon as representation begins.

## End-to-End Test

The project includes a comprehensive end-to-end integration test that simulates the complete lifecycle of a personal injury case, from intake to settlement disbursement.

### Running Integration Tests Locally

Integration tests are marked with `pytest.mark.integration` and can be run specifically:

```bash
# Run all integration tests
pytest -m integration

# Run the happy path test specifically
pytest -m integration tests/integration/test_happy_path.py
```

### Integration Test Process

The happy path integration test follows these steps:

1. **Client Intake**: Creates a client and incident via the `/intake` API endpoint
2. **Retainer Agreement**: Simulates DocuSign callback when retainer is signed
3. **Insurance Notices**: Verifies LORs are sent to insurance carriers
4. **Medical Bills**: Creates providers and medical bills, triggers damages worksheet generation
5. **Medical Records Requests**: Simulates the nightly cron job for sending record requests
6. **Demand Package**: Builds demand package from uploaded documents
7. **Settlement**: Finalizes the settlement and generates a disbursement sheet

### Nightly CI Workflow

A scheduled GitHub Actions workflow runs the integration test nightly at 02:30 UTC on the main branch. This runs the complete test suite with real services (PostgreSQL, Redis, Docassemble) to ensure the entire system functions correctly.

To view the latest test results, check the [Actions tab](https://github.com/law-and-order/pi-auto/actions/workflows/integration-test.yml) in the GitHub repository.

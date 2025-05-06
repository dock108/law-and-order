# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - YYYY-MM-DD

### Added
- **Automated Disbursement Sheet Generator & E-Sign**
  - Added database migration to extend incident table with settlement columns (settlement_amount, attorney_fee_pct, lien_total, disbursement_status).
  - Created new fee_adjustments table for tracking custom deductions/credits.
  - Implemented disbursement_calc.py utility for calculating settlement splits.
  - Added disbursement.py Celery task for generating and sending disbursement sheets.
  - Created /internal/finalize_settlement endpoint to update settlement data and queue the disbursement task.
  - Added disbursement_sheet.md Docassemble template for the disbursement statement.
  - Implemented DocuSign integration for secure e-signature of disbursement sheets.
  - Added comprehensive unit tests for calculation logic and disbursement generation.
  - Updated README.md and FLOWS.md with detailed workflow documentation.

## [1.6.0] - YYYY-MM-DD

### Added
- **Automated Demand Package Assembly**
  - Added `pikepdf` dependency for PDF manipulation.
  - Created demand package assembly system: `utils/package_rules.py`, `tasks/demand.py`, `utils/pdf_merge.py`.
  - Implemented PDF merging utility `utils.pdf_merge.merge_pdfs` for combining documents.
  - Added `is_demand_ready` function to check if an incident has all required documents for demand package creation.
  - Implemented `assemble_demand_package` Celery task to build demand packages from medical records, bills, damages worksheet, and liability photos.
  - Added `check_and_build_demand` nightly task that runs at 3 AM to find eligible incidents and create demand packages.
  - Added comprehensive unit tests for PDF merging and demand package assembly.
  - Updated documentation with demand package assembly workflow.

## [1.5.0] - YYYY-MM-DD

### Added
- **Automated Demand Package Assembly**
  - Added `pikepdf` dependency for PDF manipulation.
  - Created demand package assembly system: `utils/package_rules.py`, `tasks/demand.py`, `utils/pdf_merge.py`.
  - Implemented PDF merging utility `utils.pdf_merge.merge_pdfs` for combining documents.
  - Added `is_demand_ready` function to check if an incident has all required documents for demand package creation.
  - Implemented `assemble_demand_package` Celery task to build demand packages from medical records, bills, damages worksheet, and liability photos.
  - Added `check_and_build_demand` nightly task that runs at 3 AM to find eligible incidents and create demand packages.
  - Added comprehensive unit tests for PDF merging and demand package assembly.
  - Updated documentation with demand package assembly workflow.

## [1.4.0] - 2025-05-06
### Added
- Automated damages worksheet generation (Excel & PDF) triggered by new medical bills.
- `build_damages_worksheet` Celery task to query bills, calculate totals, generate reports (pandas, WeasyPrint), upload to storage, and update DB.
- `process_medical_bill` Celery task to handle incoming bills, record them, and trigger worksheet generation.
- Added `amount` column to `doc` table with Alembic migration for storing bill totals.
- Fallback logic to parse bill amount from filename if DB amount is missing.
- New dependencies: `pandas`, `xlsxwriter`, `weasyprint`.
- Unit tests for damages worksheet builder with mocked dependencies.
- Updated documentation (README, FLOWS.md) for the new feature.

## [1.3.0] - 2025-05-06
### Added
- Nightly medical-records request fax automation
- Celery Beat scheduler for running tasks at regular intervals
- Medical records request task that runs daily at 2:00 AM ET
- Database helper for retrieving provider payload data
- Supabase Storage integration for document uploads and signed URLs
- HIPAA-compliant medical records request letter generation
- Integration with Twilio for automated fax delivery
- Tracking of sent requests in the database
- Unit tests with mocked external services
- Updated documentation with process flow diagrams

## [1.2.0] - 2025-05-04
### Added
- Automated Letter of Representation (LOR) to insurers when retainer is signed
- DocuSign webhook endpoint to receive envelope completion notifications
- Insurance notice Celery task for asynchronous LOR generation and distribution
- Database helper to fetch insurance data for LORs
- Docassemble letter generation endpoint support
- Comprehensive unit tests for webhook and task
- Documentation of the insurance notice flow in README and FLOWS.md

## [1.1.0] - 2025-05-04
### Added
- Twilio SMS/Fax adapter with exponential backoff retry logic
- Utility functions to send SMS notifications to clients
- Utility functions to send faxes to insurance companies and providers
- Configuration settings for Twilio integration (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, etc.)
- Comprehensive unit tests with mocked Twilio API clients
- Documentation for SMS & Fax adapter usage
- Updated process flow to include SMS notifications

## [1.0.0] - 2025-05-04
### Added
- SendGrid email adapter for sending transactional emails
- Jinja2 templating engine for rendering email templates
- Email templates: welcome.html and retainer_sent.html
- SendGrid configuration in settings (SENDGRID_API_KEY)
- Comprehensive email rendering utilities
- Unit tests with mocked SendGrid API client
- Documentation for email templates and merge fields
- Updated README with Email Adapter usage section

## [0.9.0] - 2025-05-04
### Added
- Fully implemented `generate_retainer` Celery task.
- Fetches client/incident data from the database.
- Generates retainer PDF via Docassemble API integration.
- Sends retainer for e-signature via DocuSign API integration (JWT auth).
- Added `get_client_payload` DB helper.
- Created `externals` module for Docassemble and DocuSign clients.
- Added `docusign-esign` dependency.
- Included DocuSign configuration settings and `.env.sample` placeholders.
- Added unit tests for the `generate_retainer` task with mocked external services.
- Updated README and FLOWS.md with detailed retainer generation flow.

## [0.8.0] - 2025-05-04
### Added
- Celery + Redis background queue for asynchronous tasks
- Redis service with docker-compose integration
- Celery worker service for processing background tasks
- Enhanced retainer generation task that runs asynchronously
- Updated CI workflow to test Celery integration
- Extended documentation with sequence diagrams in FLOWS.md
- Unit and integration tests for the task queue

## [0.7.0] - 2025-05-04
### Added
- Client intake endpoint (`/intake`) to store client and incident data
- Database integration for client intake process
- Celery task setup for retainer agreement generation
- Comprehensive validation and error handling for the intake process
- Unit tests for the intake endpoint

## [0.6.0] - 2025-05-04
### Added
- FastAPI skeleton with health and readiness endpoints.
- Config module using pydantic-settings for environment variables management.
- Basic middleware for CORS and request ID tracking.
- Unit tests for API endpoints with mocking.
- GitHub Actions job for testing the API.
- CLI entry point for running the API (`pi-auto-api`).
- Updated README with API usage instructions.
- X-Request-ID header added to all requests/responses for tracing.

### Changed
- Updated dependencies to include FastAPI, Uvicorn, and HTTPX.
- Added API badge to README.

## [0.5.0] - 2025-05-04
### Added
- Retainer agreement interview in Docassemble.
- Document generation API for automated PDF creation.
- Flask wrapper for Docassemble integration.
- API endpoint for generating retainer agreements.
- Integration tests for document generation.
- Extended health check script to test the API.
- Documentation for API usage and template mapping.

## [0.4.0] - 2025-05-04
### Added
- Dockerized Docassemble stack.
- Docker Compose setup for Docassemble and PostgreSQL.
- Bind-mount for templates directory into Docassemble container.
- Health check script for Docassemble.
- CI integration for testing Docassemble setup.
- Documentation for Docassemble integration in README.md and TEMPLATE_REFERENCE.md.

## [0.3.1] - 2025-05-04
### Added
- Row-Level Security (RLS) test suite (`tests/test_rls.py`) using `asyncpg`.
- PostgreSQL service container and seeding to CI workflow for RLS testing.
- Coverage reporting (`--cov`) added to pytest configuration and CI.
- `docs/SCHEMA.md` with RLS testing documentation.

### Changed
- Updated `README.md` testing section.
- Updated CI workflow for database testing and coverage checks.
- Alembic `env.py` modified to rely on Alembic's async runner.

## [0.3.0] - 2025-05-04
### Added
- Initial database schema migration (`0001_initial_schema.py`) with tables (`client`, `incident`, `insurance`, `provider`, `doc`, `task`) and basic RLS policies.
- SQLAlchemy ORM models (`src/pi_auto/db/models.py`).
- Basic CRUD operations module (`src/pi_auto/db/crud.py`).
- Unit tests for CRUD operations (`tests/test_crud.py`) using SQLite.
- Unit tests for database engine (`tests/test_db.py`) using mocks.
- Integration tests for models (`tests/test_models.py`) using SQLite.
- Documentation for CRUD operations (`docs/CRUD_REFERENCE.md`).

### Changed
- Updated `README.md` with database setup information.
- Configured `pytest` and related dependencies (`pytest-asyncio`, `asyncpg`, `greenlet`).
- Configured pre-commit hooks for linting, formatting, and testing.

## [0.2.0] - 2025-05-04

### Added
- Centralized template system in `templates/` directory
- Jinja-style template tags for all document templates
- PII detection script to ensure no real client information exists in templates
- Template reference documentation in `docs/TEMPLATE_REFERENCE.md`
- Organized templates by purpose (intake, correspondence, medical, settlement, workflow)
- Template unit tests to verify PII compliance

## [0.1.0] - 2025-05-04

### Added

- Initial project setup with Poetry for dependency management
- Implemented src layout structure
- Added CI pipeline with GitHub Actions (Python 3.11, linting, formatting, testing)
- Set up dev tooling (ruff, black, isort, pre-commit hooks)
- Created documentation framework (README.md, CHANGELOG.md)
- Added template system with Jinja-style tags
- Created template directory structure organized by purpose
- Created PII detection script for templates
- Added template examples for various legal documents
- Implemented TEMPLATE_REFERENCE.md for tag documentation
- Created database schema for client, incident, insurance, provider, doc, and task tables
- Set up Alembic migration system with async support
- Implemented Row-Level Security policies
- Added SQLAlchemy ORM models
- Created database connection management utilities
- Implemented CRUD operations with comprehensive test coverage
- Added documentation for database operations (CRUD_REFERENCE.md)

### Fixed

- Issue with CI configuration
- Git configuration for proper line endings
- Pre-commit hooks configuration

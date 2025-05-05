# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-05-13
### Added
- Automated Letter of Representation (LOR) to insurers when retainer is signed
- DocuSign webhook endpoint to receive envelope completion notifications
- Insurance notice Celery task for asynchronous LOR generation and distribution
- Database helper to fetch insurance data for LORs
- Docassemble letter generation endpoint support
- Comprehensive unit tests for webhook and task
- Documentation of the insurance notice flow in README and FLOWS.md

## [1.1.0] - 2025-05-12
### Added
- Twilio SMS/Fax adapter with exponential backoff retry logic
- Utility functions to send SMS notifications to clients
- Utility functions to send faxes to insurance companies and providers
- Configuration settings for Twilio integration (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, etc.)
- Comprehensive unit tests with mocked Twilio API clients
- Documentation for SMS & Fax adapter usage
- Updated process flow to include SMS notifications

## [1.0.0] - 2025-05-11
### Added
- SendGrid email adapter for sending transactional emails
- Jinja2 templating engine for rendering email templates
- Email templates: welcome.html and retainer_sent.html
- SendGrid configuration in settings (SENDGRID_API_KEY)
- Comprehensive email rendering utilities
- Unit tests with mocked SendGrid API client
- Documentation for email templates and merge fields
- Updated README with Email Adapter usage section

## [0.9.0] - 2025-05-10
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

## [0.8.0] - 2025-05-10
### Added
- Celery + Redis background queue for asynchronous tasks
- Redis service with docker-compose integration
- Celery worker service for processing background tasks
- Enhanced retainer generation task that runs asynchronously
- Updated CI workflow to test Celery integration
- Extended documentation with sequence diagrams in FLOWS.md
- Unit and integration tests for the task queue

## [0.7.0] - 2025-05-05
### Added
- Client intake endpoint (`/intake`) to store client and incident data
- Database integration for client intake process
- Celery task setup for retainer agreement generation
- Comprehensive validation and error handling for the intake process
- Unit tests for the intake endpoint

## [0.6.0] - 2025-05-05
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

## [0.5.0] - 2025-05-05
### Added
- Retainer agreement interview in Docassemble.
- Document generation API for automated PDF creation.
- Flask wrapper for Docassemble integration.
- API endpoint for generating retainer agreements.
- Integration tests for document generation.
- Extended health check script to test the API.
- Documentation for API usage and template mapping.

## [0.4.0] - 2025-05-05
### Added
- Dockerized Docassemble stack.
- Docker Compose setup for Docassemble and PostgreSQL.
- Bind-mount for templates directory into Docassemble container.
- Health check script for Docassemble.
- CI integration for testing Docassemble setup.
- Documentation for Docassemble integration in README.md and TEMPLATE_REFERENCE.md.

## [0.3.1] - 2025-05-05
### Added
- Row-Level Security (RLS) test suite (`tests/test_rls.py`) using `asyncpg`.
- PostgreSQL service container and seeding to CI workflow for RLS testing.
- Coverage reporting (`--cov`) added to pytest configuration and CI.
- `docs/SCHEMA.md` with RLS testing documentation.

### Changed
- Updated `README.md` testing section.
- Updated CI workflow for database testing and coverage checks.
- Alembic `env.py` modified to rely on Alembic's async runner.

## [0.3.0] - 2025-05-05
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

## [0.2.0] - 2025-05-05

### Added
- Centralized template system in `templates/` directory
- Jinja-style template tags for all document templates
- PII detection script to ensure no real client information exists in templates
- Template reference documentation in `docs/TEMPLATE_REFERENCE.md`
- Organized templates by purpose (intake, correspondence, medical, settlement, workflow)
- Template unit tests to verify PII compliance

## [0.1.0] - 2025-05-05

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

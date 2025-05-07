# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.6.0] - 2024-07-31

### Added

- **API ↔ SDK Contract Testing**:
  - Added `schemathesis[pytest]` for OpenAPI conformance testing against live FastAPI app (`tests/contract/test_api_client_contract.py`).
  - Implemented a smoke test layer to verify parity between direct API calls and TypeScript SDK calls (invoked via Node.js subprocess `tests/contract/sdk_invoker.js`) for key implemented endpoints (e.g., `/auth/login`).
  - Added `openapi-diff` for lightweight Pact-style checking of spec changes against the live app schema during CI.
  - New GitHub Actions workflow `contract-tests.yml` that:
    - Runs on backend, OpenAPI, or SDK changes.
    - Sets up Python, Node, and services (Postgres, Redis).
    - Regenerates SDK, runs `openapi-diff`, starts the API, and executes `pytest -m contract`.
- **Developer Documentation**:
  - Created a comprehensive "Getting Started" guide (`docs/DEVELOPMENT.md`) covering prerequisites, full-stack local setup, running tests/linters, common environment variables, and troubleshooting tips.

### Changed

- Updated `README.md` to include a link to the new `DEVELOPMENT.md` guide and a CI badge for the "Contract Tests" workflow.
- Added `contract` marker to `pyproject.toml` for pytest.

## [2.5.0] - 2024-07-31

### Added

- **Mono-repo Restructuring**:
  - Reshaped the project into a pnpm mono-repo with `apps/*` and `packages/*` workspaces.
  - Scaffolded a Next.js 14 application in `apps/web` (TypeScript, ESLint, Tailwind, App Router, src directory).
    - Includes a basic homepage (`src/app/page.tsx`) and a health check API route (`src/app/api/health/route.ts`).
    - Configured `next.config.mjs` with `output: 'standalone'` and to transpile shared packages.
  - Created a shared React component package `packages/ui` (`@pi-monorepo/ui`).
    - Includes a simple `Button` component.
  - Wired `apps/web` to import from `packages/ui` using TypeScript path aliases.
  - Added Jest and React Testing Library to `apps/web` with a smoke test for the homepage.
- **Path-Filtered GitHub Actions**:
  - Renamed existing CI workflow to `backend.yml` and configured it to ignore paths related to `apps/`, `packages/ui/`, and `packages/api-client/`.
  - Created a new `frontend.yml` workflow that runs on changes to `apps/web/**` or `packages/ui/**`.
    - This workflow installs dependencies, lints, builds, and tests the `apps/web` application.

### Changed

- Updated root `package.json` to define pnpm workspaces.
- Updated `README.md` with new directory structure, CI badges, and setup/run instructions for both backend and frontend.

## [2.4.0] - 2025-05-07

### Added

- **CI Template Guard**: Implemented a CI job (`Template Guard`) that runs as part of the test suite (`pytest -m template_guard`).
  - Moved PII check logic from `scripts/check_templates.py` to `tests/template_guard.py`.
  - Enhanced guard to fail on:
    - Potential PII (Names, Phones, Dates, SSNs) using regex.
    - Unwrapped dollar amounts (e.g., `$100` outside `{{ }}`).
    - Empty Jinja tags (`{{ }}`).
    - Undefined Jinja tags (not found in `docs/TEMPLATE_REFERENCE.md`).
  - Added test `tests/template_guard.py::test_guard_catches_violations` to verify guard logic using a temporary bad template.
  - Updated CI workflow (`.github/workflows/ci.yml`) to run the guard before main tests.
  - Updated `README.md` with instructions for the template guard.

### Removed

- Deleted old script `scripts/check_templates.py`.
- Removed corresponding `check-templates` hook from `.pre-commit-config.yaml`.

## [2.3.0] - 2025-05-07

### Added

- **Live Activity Feed via Server-Sent Events (SSE)**
  - Redis channel convention: `activity` (single channel for now).
  - Event helper `src/pi_auto_api/events.py` with `record_event(event: dict)` to publish JSON events to Redis.
  - SSE endpoint `src/pi_auto_api/routers/sse.py` at `GET /api/events/stream`:
    - Subscribes to the `activity` Redis channel.
    - Yields `text/event-stream` lines: `id:<timestamp>\ndata:<json>\n\n`.
    - Ignores `Last-Event-ID` header (for v1).
    - Sends a heartbeat comment `: keep-alive\n\n` every 30 seconds.
  - Mounted SSE router in `main.py`.
  - Hooked `record_event({"type":"disbursement_sent","incident_id":...})` into the `generate_disbursement_sheet` Celery task.
  - Unit/integration tests in `tests/test_sse.py` using `httpx.AsyncClient`:
    - Verified event reception from Redis publish.
    - Ensured heartbeat arrival (with mocked `asyncio.sleep`).
    - Tested graceful client disconnect handling.
  - Updated `openapi/pi-workflow.yaml` with the `/api/events/stream` path (text/event-stream response, Last-Event-ID header).
  - Regenerated TypeScript client SDK (`pnpm run gen:client`).

### Changed

- Migrated Redis interactions from the deprecated `aioredis` library to the async API provided by `redis` (>=4.2) library.

## [2.2.0] - 2025-05-07

### Added

- Staff JWT-based authentication flow.
  - `Staff` SQLAlchemy model with `first_name`, `last_name`, `email`, `hashed_password`, `is_active`, `is_superuser`, `created_at`, `updated_at` fields, and a `full_name` hybrid property.
  - `JWT_SECRET` and `JWT_EXP_MINUTES` settings in `config.py` and `.env.sample`.
  - Auth helpers in `src/pi_auto_api/auth.py`:
    - `create_access_token` for generating HS256 JWTs.
    - `verify_password` and `get_password_hash` using `passlib[bcrypt]`.
    - `get_current_staff` FastAPI dependency to authenticate users via Bearer token.
  - `/auth/login` API endpoint (`POST`) for staff to log in with email and password, returning an access token.
  - Protected existing stub routes in `pi_workflow.py` (`/api/cases`, `/api/tasks`, `/api/documents`) using the `get_current_staff` dependency.
  - Unit tests in `tests/test_auth_login.py` covering successful login, inactive user login, wrong password, non-existent user, and protected route access (with and without token).
  - Updated `openapi/pi-workflow.yaml` with:
    - `AuthLoginRequest` and `AuthLoginResponse` schemas.
    - `HTTPError` schema for generic error responses.
    - `BearerAuth` security scheme (JWT).
    - `/auth/login` path definition.
    - Applied `BearerAuth` security to all `/api/*` pi-workflow routes.
  - Regenerated TypeScript client SDK (`pnpm run gen:client`).
  - Updated `README.md` with a "Staff Authentication" section and `curl` examples.

### Fixed

- Corrected import paths in `src/pi_auto_api/auth.py` to align with project structure (`pi_auto` vs `pi_auto_api` packages).
- Ensured `get_staff_by_email` in `src/pi_auto/db/crud.py` is `async` and updated `auth.py` to use `AsyncSession` and `await` accordingly.

### Known Issues

- **Alembic Migration for `staff` table**: The generation of the Alembic migration for the `staff` table is currently blocked by a persistent "Can't locate revision identified by '0001'" error. This needs to be resolved by ensuring the target database (as per `sqlalchemy.url`) is clean from Alembic's perspective (e.g., no stale `alembic_version` table or an empty one) before attempting `alembic revision --autogenerate` again. (Deliverable 1.1 pending this resolution).
- **RLS Policies**: Row Level Security policies for existing tables (Deliverable 1.2) have been drafted conceptually but not yet implemented in an Alembic migration due to the above issue.

## [2.1.0] - 2025-05-07

### Added

- Environment variable `ALLOWED_ORIGINS` (default `http://localhost:3000`) to control CORS.
- CORS middleware in `main.py` using `ALLOWED_ORIGINS` setting.
- Unit tests (`tests/test_cors.py`) for CORS pre-flight and standard requests from allowed/disallowed origins.
- Updated `README.md` with CORS configuration details.

## [2.0.0] - 2025-05-07

### Added

- Generated TypeScript API client SDK (`packages/api-client`) from OpenAPI spec using `openapi-typescript`.
- Set up pnpm workspaces for monorepo structure (`package.json`, `.npmrc`).
- Added `gen:client` script to regenerate the SDK.
- Included minimal `tsconfig.json` for the SDK package.
- Added "Client SDK Sync" CI job to:
  - Install Node.js/pnpm.
  - Run `pnpm install`.
  - Regenerate the client (`pnpm run gen:client`).
  - Type check the client (`pnpm tsc`).
  - Check for drift using `git diff --exit-code`.
- Added Python smoke test (`tests/test_sdk_placeholder.py`) to verify SDK package resolution via Node.js.
- Updated `README.md` with SDK installation and usage instructions.

### Changed

- Moved OpenAPI validation in `tests/test_api_spec.py` to use `openapi-spec-validator`.

### Removed

- Temporarily disabled `tests/test_retainer_api.py::test_retainer_generation` due to freezing (marked as skipped).

## [1.9.0] - 2025-05-07

### Added

- Initial OpenAPI 3.1 spec (`openapi/pi-workflow.yaml`) defining core resources (Cases, Tasks, Documents, Activity Events) with empty schemas.
- Stub FastAPI router (`src/pi_auto_api/routers/pi_workflow.py`) for the defined OpenAPI paths, all returning 501 Not Implemented.
- Mounted the new router in `main.py` under the `/api` prefix.
- Script `scripts/export_openapi.py` to generate/update the OpenAPI spec from FastAPI app, with a `--check` option for CI.
- CI step in `ci.yml` to run `export_openapi.py --check` and fail on drift.
- Unit tests (`tests/test_api_spec.py`) to:
  - Assert each stub route returns 501.
  - Validate `openapi/pi-workflow.yaml` using `openapi-schema-validator`.
- Updated `README.md` with an "API spec" section linking to the YAML and showing a `curl` example.

## [1.8.0] - YYYY-MM-DD

### Added

- **Full Happy-Path Integration Test & Nightly CI**
  - Created comprehensive end-to-end integration test simulating the entire PI case lifecycle.
  - Added test fixtures for mocking external services (Docassemble, DocuSign, Twilio, SendGrid).
  - Implemented database session with transaction rollback for clean test isolation.
  - Created Celery eager execution fixture for synchronous task testing.
  - Added GitHub Actions workflow for nightly integration testing (runs at 02:30 UTC).
  - Set up CI for full test environment with PostgreSQL, Redis, and Docassemble services.
  - Added JUnit and coverage report generation and artifact publishing.
  - Updated README with details on running integration tests locally.

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
  - Implemented PDF merging utility `utils.pdf_merge.merge_pdfs`

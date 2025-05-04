# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

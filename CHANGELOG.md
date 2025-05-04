# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-05-05

### Added
- Centralized template system in `templates/` directory
- Jinja-style template tags for all document templates
- PII detection script to ensure no real client information exists in templates
- Template reference documentation in `docs/TEMPLATE_REFERENCE.md`
- Organized templates by purpose (intake, correspondence, medical, settlement, workflow)
- Template unit tests to verify PII compliance

## [0.1.0] - 2024-05-05

### Added
- Initial repository setup with Poetry
- Source layout (src/pi_auto)
- Testing scaffold with pytest
- CI/CD pipeline with GitHub Actions
- Code quality tools (ruff, black, isort)
- Pre-commit hooks configuration

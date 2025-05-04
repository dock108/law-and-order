# Personal Injury Automation

[![CI](https://github.com/law-and-order/pi-auto/actions/workflows/ci.yml/badge.svg)](https://github.com/law-and-order/pi-auto/actions/workflows/ci.yml)

A comprehensive set of tools for automating personal injury case management and workflows.

## Requirements

- Python 3.11+
- Poetry

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/your-org/pi-auto.git
cd pi-auto
```

2. Install dependencies:

```bash
poetry install
```

3. Activate the virtual environment:

```bash
poetry shell
```

4. Run tests:

```bash
pytest
```

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

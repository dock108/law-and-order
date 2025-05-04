# Personal Injury Automation

[![CI](https://github.com/your-org/pi-auto/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/pi-auto/actions/workflows/ci.yml)

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

## License

Proprietary - All Rights Reserved

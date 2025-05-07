# Developer Getting Started Guide

This guide will help you set up your local development environment for the Personal Injury Automation project, allowing you to run the full stack (FastAPI backend and Next.js frontend) and contribute to the codebase.

## 1. Prerequisites

Make sure you have the following software installed on your system:

- **Python**: Version 3.11 or 3.12. We recommend using a version manager like `pyenv`.
- **Poetry**: For Python package management. Follow the [official installation guide](https://python-poetry.org/docs/#installation).
- **pnpm**: For Node.js package management in the monorepo. Follow the [official installation guide](https://pnpm.io/installation).
- **Node.js**: Version 18.x or later (pnpm will manage this if you have a core Node.js version installed).
- **Docker & Docker Compose**: For running external services like PostgreSQL, Redis, and Docassemble. [Install Docker Desktop](https://www.docker.com/products/docker-desktop/) or the Docker Engine and Docker Compose plugin separately.

## 2. Quick Start: Setup & Running the Full Stack

Follow these steps to get the application running locally:

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/law-and-order/pi-auto.git # Replace with your fork/actual repo URL if different
    cd pi-auto
    ```

2.  **Install All Dependencies**:
    This single command will install both Python (backend) and Node.js (frontend, SDK, UI library) dependencies.

    ```bash
    pnpm install
    ```

    _Behind the scenes, `pnpm install` in the root will also trigger `poetry install` for the Python backend due to pnpm workspace setup (if configured, otherwise run `poetry install` separately as shown below)._

    If `pnpm install` doesn't automatically run `poetry install` (check your `package.json` scripts or monorepo tool's capabilities), run it explicitly:

    ```bash
    poetry install
    ```

3.  **Start External Services with Docker Compose**:
    This command starts PostgreSQL, Redis, and Docassemble containers in detached mode.

    ```bash
    docker compose up -d
    ```

    You can check the status of the containers with `docker ps`.

4.  **Activate Python Virtual Environment**:

    ```bash
    poetry shell
    ```

    All subsequent Python-related commands should be run within this shell.

5.  **Run Database Migrations** (inside `poetry shell`):
    Ensure your database schema is up to date.

    ```bash
    alembic upgrade head
    ```

    _Note: You might need to copy `.env.sample` to `.env` and configure `SUPABASE_URL` (which is your `DATABASE_URL`) for Alembic to connect to the Dockerized PostgreSQL instance (e.g., `postgresql://testuser:testpassword@localhost:5432/testdb`)._

6.  **Start the FastAPI Backend API** (inside `poetry shell`):

    ```bash
    poetry run uvicorn pi_auto_api.main:app --reload
    ```

    The API will typically be available at `http://localhost:8000` (or `http://localhost:9000` if you use that port from README, ensure consistency).

7.  **Start the Next.js Frontend Application** (in a **new terminal window/tab**):
    ```bash
    pnpm -C apps/web dev
    ```
    The Next.js frontend will typically be available at `http://localhost:3000`.

You should now have the full stack running!

- Backend API: `http://localhost:8000/docs`
- Frontend UI: `http://localhost:3000`

## 3. Running Tests & Linters

### Backend (Python)

Make sure you are inside the `poetry shell`.

- **Run all Pytests (including coverage)**:
  ```bash
  pytest
  ```
- **Run Template Guard tests**:
  ```bash
  pytest -m template_guard
  ```
- **Run Contract tests (API vs SDK)**:

  ```bash
  pytest -m contract
  ```

  _(Requires the FastAPI dev server to be running at the address configured in `tests/contract/sdk_invoker.js`)_

- **Run Linters/Formatters (via pre-commit)**:
  To run all pre-commit hooks on all files:
  ```bash
  poetry run pre-commit run --all-files
  ```
  To install pre-commit hooks to run automatically before each commit:
  ```bash
  poetry run pre-commit install
  ```

### Frontend (TypeScript/Next.js)

These commands can be run from the project root.

- **Run ESLint**:
  ```bash
  pnpm -C apps/web lint
  ```
- **Run Jest tests**:
  ```bash
  pnpm -C apps/web test
  ```
- **Run Prettier (format check for all supported files in monorepo)**:
  ```bash
  pnpm format:check
  ```
  To automatically format:
  ```bash
  pnpm format
  ```

## 4. Common Environment Variables

Create a `.env` file in the project root by copying `.env.sample`. Key variables include:

- `SUPABASE_URL`: PostgreSQL connection string (e.g., `postgresql://testuser:testpassword@localhost:5432/testdb` for local Docker setup).
- `SUPABASE_KEY`: A dummy key is often sufficient for local development if not using Supabase Auth services directly, but ensure it's set.
- `REDIS_URL`: Redis connection string (e.g., `redis://localhost:6379/0` for local Docker setup).
- `ALLOWED_ORIGINS`: Comma-separated list of URLs allowed for CORS (e.g., `http://localhost:3000,http://127.0.0.1:3000`).
- `JWT_SECRET`: A strong, random secret key for JWT signing. Generate one and keep it safe.
- `DOCASSEMBLE_URL`: URL for your Docassemble instance (e.g., `http://localhost:8100` if running Docker setup from this repo).
- `SENDGRID_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, etc.: API keys for external services.

**For Contract Tests (`sdk_invoker.js`)**:

- `API_BASE_URL_FOR_SDK_TESTS`: If your FastAPI app runs on a different port than the default `http://localhost:8000` during contract tests, set this for the Node.js script.

## 5. Hot-Reloading & Troubleshooting

- **FastAPI Backend**: `--reload` in the `uvicorn` command enables hot-reloading for backend Python code changes.
- **Next.js Frontend**: `pnpm -C apps/web dev` enables Fast Refresh for frontend React code changes.
- **SDK Changes**: If you modify `openapi/pi-workflow.yaml`, you need to regenerate the API client:
  ```bash
  pnpm gen:client
  ```
- **Dependency Issues**:
  - If Python dependencies seem off, try: `poetry lock` then `poetry install`.
  - If Node dependencies seem off, try: `pnpm install` (possibly with `--force` or by deleting `node_modules` and `pnpm-lock.yaml` first, as a last resort).
- **Docker Services**:
  - Check logs: `docker compose logs -f <service_name>` (e.g., `postgres`, `redis`).
  - Ensure ports are not conflicting with other local services.
- **`template_guard` fails**: Check `templates/` or `email_templates/` for hardcoded PII, empty merge fields, or tags not in `docs/TEMPLATE_REFERENCE.md`.
- **`contract` tests fail**:
  - Ensure the FastAPI dev server is running and accessible to the Node.js script.
  - Check for discrepancies between `openapi/pi-workflow.yaml` and actual API behavior or SDK generation.

Happy coding!

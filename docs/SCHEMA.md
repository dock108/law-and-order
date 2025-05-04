# Database Schema

This document outlines the database schema used by the PI Automation project.

The database is managed using PostgreSQL and utilizes SQLAlchemy for ORM interactions and Alembic for migrations.

## Tables

- `client`: Stores information about clients.
- `incident`: Details about specific personal injury incidents.
- `insurance`: Insurance policy information related to an incident.
- `provider`: Medical providers associated with an incident.
- `doc`: Documents related to an incident (e.g., medical records, police reports).
- `task`: Tasks associated with managing an incident case.

(Refer to `src/pi_auto/db/models.py` for detailed column definitions and relationships.)

## Row-Level Security (RLS)

The database employs Row-Level Security (RLS) policies to ensure data privacy and restrict access based on user roles (`lawyer`, `paralegal`, `client`) and associations (e.g., task assignee, client owner).

Policies generally allow:
- `lawyer` role: Access to all data.
- `paralegal` role: Access to tasks assigned to them and related incident/client data.
- `client` role: Access to their own client record and associated incident/task/doc data.
- `anon` (unauthenticated): No access.

(Refer to the `0001_initial_schema.py` migration file for the specific policy definitions.)

### RLS Testing

Row-Level Security policies are tested rigorously to ensure they function as expected.

- **CI Environment:** The GitHub Actions workflow (`.github/workflows/ci.yml`) spins up a dedicated PostgreSQL container for each test run.
- **Migrations & Seeding:** The CI job automatically applies all database migrations and then runs `seed.sql` to populate the test database with specific users (lawyer, paralegals, clients) and associated records.
- **Test Suite:** The `tests/test_rls.py` suite uses `asyncpg` to connect to the test database, simulating different user roles by setting appropriate session variables (role and JWT claims).
- **Verification:** Tests verify both "happy path" scenarios (users accessing data they *should* see) and "blocked path" scenarios (users being correctly denied access to data they *should not* see).
- **Coverage:** Test coverage, including RLS tests, is measured and enforced to be above 80%.

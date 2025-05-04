"""Initial schema for PI Automation.

Revision ID: 0001
Revises:
Create Date: 2024-05-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the database schema changes for this migration."""
    # Create client table
    op.create_table(
        "client",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("dob", sa.Date, nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False
        ),
    )

    # Create incident table
    op.create_table(
        "incident",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "client_id",
            sa.Integer,
            sa.ForeignKey("client.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=True),
        sa.Column("location", sa.Text, nullable=True),
        sa.Column("police_report_url", sa.String(255), nullable=True),
        sa.Column("injuries", sa.JSON, nullable=True),
        sa.Column("vehicle_damage_text", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False
        ),
    )

    # Create insurance table
    op.create_table(
        "insurance",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "incident_id",
            sa.Integer,
            sa.ForeignKey("incident.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("carrier_name", sa.String(255), nullable=False),
        sa.Column("policy_number", sa.String(100), nullable=True),
        sa.Column("claim_number", sa.String(100), nullable=True),
        sa.Column("is_client_side", sa.Boolean, nullable=False, default=False),
        sa.Column(
            "created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False
        ),
    )

    # Create provider table
    op.create_table(
        "provider",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "incident_id",
            sa.Integer,
            sa.ForeignKey("incident.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("fax", sa.String(50), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False
        ),
    )

    # Create doc table
    op.create_table(
        "doc",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "incident_id",
            sa.Integer,
            sa.ForeignKey("incident.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("url", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column(
            "created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False
        ),
    )

    # Create task table
    op.create_table(
        "task",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "incident_id",
            sa.Integer,
            sa.ForeignKey("incident.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("assignee_email", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False
        ),
    )

    # Enable Row-Level Security (RLS) on all tables
    # Enable RLS on client table
    op.execute("ALTER TABLE client ENABLE ROW LEVEL SECURITY;")
    # Enable RLS on incident table
    op.execute("ALTER TABLE incident ENABLE ROW LEVEL SECURITY;")
    # Enable RLS on insurance table
    op.execute("ALTER TABLE insurance ENABLE ROW LEVEL SECURITY;")
    # Enable RLS on provider table
    op.execute("ALTER TABLE provider ENABLE ROW LEVEL SECURITY;")
    # Enable RLS on doc table
    op.execute("ALTER TABLE doc ENABLE ROW LEVEL SECURITY;")
    # Enable RLS on task table
    op.execute("ALTER TABLE task ENABLE ROW LEVEL SECURITY;")

    # Create RLS policies for lawyers and paralegals
    # Client table policy
    op.execute(
        """
        CREATE POLICY client_policy ON client
        USING (
            (auth.jwt() ->> 'role') IN ('lawyer', 'paralegal')
            OR
            (email = (auth.jwt() ->> 'email'))
        );
    """
    )

    # Incident table policy
    op.execute(
        """
        CREATE POLICY incident_policy ON incident
        USING (
            (auth.jwt() ->> 'role') IN ('lawyer', 'paralegal')
            OR
            EXISTS (
                SELECT 1 FROM client
                WHERE client.id = incident.client_id
                AND client.email = (auth.jwt() ->> 'email')
            )
        );
    """
    )

    # Insurance table policy
    op.execute(
        """
        CREATE POLICY insurance_policy ON insurance
        USING (
            (auth.jwt() ->> 'role') IN ('lawyer', 'paralegal')
            OR
            EXISTS (
                SELECT 1 FROM incident
                JOIN client ON client.id = incident.client_id
                WHERE incident.id = insurance.incident_id
                AND client.email = (auth.jwt() ->> 'email')
            )
        );
    """
    )

    # Provider table policy
    op.execute(
        """
        CREATE POLICY provider_policy ON provider
        USING (
            (auth.jwt() ->> 'role') IN ('lawyer', 'paralegal')
            OR
            EXISTS (
                SELECT 1 FROM incident
                JOIN client ON client.id = incident.client_id
                WHERE incident.id = provider.incident_id
                AND client.email = (auth.jwt() ->> 'email')
            )
        );
    """
    )

    # Doc table policy
    op.execute(
        """
        CREATE POLICY doc_policy ON doc
        USING (
            (auth.jwt() ->> 'role') IN ('lawyer', 'paralegal')
            OR
            EXISTS (
                SELECT 1 FROM incident
                JOIN client ON client.id = incident.client_id
                WHERE incident.id = doc.incident_id
                AND client.email = (auth.jwt() ->> 'email')
            )
        );
    """
    )

    # Task table policy
    op.execute(
        """
        CREATE POLICY task_policy ON task
        USING (
            (auth.jwt() ->> 'role') IN ('lawyer', 'paralegal')
            OR
            (assignee_email = (auth.jwt() ->> 'email'))
            OR
            EXISTS (
                SELECT 1 FROM incident
                JOIN client ON client.id = incident.client_id
                WHERE incident.id = task.incident_id
                AND client.email = (auth.jwt() ->> 'email')
            )
        );
    """
    )

    # Create helper function to create test users
    op.execute(
        """
    CREATE OR REPLACE FUNCTION create_test_users()
    RETURNS VOID AS $$
    BEGIN
        -- Create lawyer role user
        INSERT INTO auth.users (id, email, role)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'lawyer@example.com',
            'lawyer'
        )
        ON CONFLICT (id) DO NOTHING;

        -- Create paralegal role user
        INSERT INTO auth.users (id, email, role)
        VALUES (
            '00000000-0000-0000-0000-000000000002',
            'paralegal@example.com',
            'paralegal'
        )
        ON CONFLICT (id) DO NOTHING;

        -- Create client role user
        INSERT INTO auth.users (id, email, role)
        VALUES (
            '00000000-0000-0000-0000-000000000003',
            'client@example.com',
            'client'
        )
        ON CONFLICT (id) DO NOTHING;
    END;
    $$ LANGUAGE plpgsql;
    """
    )


def downgrade() -> None:
    """Revert the database schema changes made by this migration."""
    # Drop the helper function
    op.execute("DROP FUNCTION IF EXISTS create_test_users();")

    # Drop tables in reverse order of creation (to handle foreign key constraints)
    op.drop_table("task")
    op.drop_table("doc")
    op.drop_table("provider")
    op.drop_table("insurance")
    op.drop_table("incident")
    op.drop_table("client")

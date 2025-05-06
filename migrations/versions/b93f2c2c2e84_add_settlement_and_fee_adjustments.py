"""add_settlement_and_fee_adjustments.

Revision ID: b93f2c2c2e84
Revises: a8ffc5416e84
Create Date: 2025-05-07 14:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b93f2c2c2e84"
down_revision: Union[str, None] = "a8ffc5416e84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the migration: add settlement columns and fee_adjustments table."""
    # Add columns to incident table
    op.add_column(
        "incident",
        sa.Column(
            "settlement_amount", sa.NUMERIC(precision=10, scale=2), nullable=True
        ),
    )
    op.add_column(
        "incident",
        sa.Column(
            "attorney_fee_pct",
            sa.NUMERIC(precision=5, scale=2),
            nullable=False,
            server_default="33.33",
        ),
    )
    op.add_column(
        "incident",
        sa.Column(
            "lien_total",
            sa.NUMERIC(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "incident",
        sa.Column(
            "disbursement_status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
    )

    # Create fee_adjustments table
    op.create_table(
        "fee_adjustments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "incident_id",
            sa.Integer,
            sa.ForeignKey("incident.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("amount", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False
        ),
    )

    # Enable RLS on fee_adjustments table
    op.execute("ALTER TABLE fee_adjustments ENABLE ROW LEVEL SECURITY;")

    # Create policies for fee_adjustments table
    op.execute(
        """
        CREATE POLICY lawyer_all_fee_adjustments ON fee_adjustments
        FOR ALL
        TO lawyer
        USING (true);
        """
    )
    op.execute(
        """
        CREATE POLICY paralegal_all_fee_adjustments ON fee_adjustments
        FOR ALL
        TO paralegal
        USING (true);
        """
    )
    op.execute(
        """
        CREATE POLICY client_read_own_fee_adjustments ON fee_adjustments
        FOR SELECT
        TO client
        USING (
            EXISTS (
                SELECT 1 FROM incident i
                JOIN client c ON i.client_id = c.id
                WHERE fee_adjustments.incident_id = i.id
                AND c.id::text = (auth.jwt()->'sub')::text
            )
        );
        """
    )
    op.execute(
        """
        CREATE POLICY anon_no_access_fee_adjustments ON fee_adjustments
        FOR ALL
        TO anon
        USING (false);
        """
    )


def downgrade() -> None:
    """Revert the migration: remove settlement columns and fee_adjustments table."""
    # Drop fee_adjustments table
    op.drop_table("fee_adjustments")

    # Remove columns from incident table
    op.drop_column("incident", "disbursement_status")
    op.drop_column("incident", "lien_total")
    op.drop_column("incident", "attorney_fee_pct")
    op.drop_column("incident", "settlement_amount")

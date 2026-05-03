"""Track refactor plan identity and operation order.

Revision ID: 20260503_0002
Revises: 20260502_0001
Create Date: 2026-05-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260503_0002"
down_revision: str | None = "20260502_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("refactor_runs", sa.Column("plan_id", sa.String(length=32), nullable=True))
    op.execute("UPDATE refactor_runs SET plan_id = 'plan_' || id WHERE plan_id IS NULL")
    op.alter_column("refactor_runs", "plan_id", nullable=False)
    op.create_index("ix_refactor_runs_plan_id", "refactor_runs", ["plan_id"], unique=True)

    op.add_column(
        "memory_operations",
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_memory_operations_run_position", "memory_operations", ["refactor_run_id", "position"])


def downgrade() -> None:
    op.drop_index("ix_memory_operations_run_position", table_name="memory_operations")
    op.drop_column("memory_operations", "position")

    op.drop_index("ix_refactor_runs_plan_id", table_name="refactor_runs")
    op.drop_column("refactor_runs", "plan_id")

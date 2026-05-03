"""Add review decisions.

Revision ID: 20260503_0006
Revises: 20260503_0005
Create Date: 2026-05-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260503_0006"
down_revision: str | None = "20260503_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_decisions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column(
            "refactor_run_id",
            sa.String(length=32),
            sa.ForeignKey("refactor_runs.id"),
            nullable=False,
        ),
        sa.Column(
            "operation_id",
            sa.String(length=32),
            sa.ForeignKey("memory_operations.id"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_review_decisions_refactor_run_id", "review_decisions", ["refactor_run_id"])
    op.create_index("ix_review_decisions_operation_id", "review_decisions", ["operation_id"])
    op.create_index("ix_review_decisions_decision", "review_decisions", ["decision"])


def downgrade() -> None:
    op.drop_index("ix_review_decisions_decision", table_name="review_decisions")
    op.drop_index("ix_review_decisions_operation_id", table_name="review_decisions")
    op.drop_index("ix_review_decisions_refactor_run_id", table_name="review_decisions")
    op.drop_table("review_decisions")

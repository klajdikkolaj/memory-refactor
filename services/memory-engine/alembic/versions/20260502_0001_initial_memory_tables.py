"""Initial memory tables.

Revision ID: 20260502_0001
Revises:
Create Date: 2026-05-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260502_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "memory_units",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_memory_units_kind", "memory_units", ["kind"])
    op.create_index("ix_memory_units_status", "memory_units", ["status"])

    op.create_table(
        "memory_sources",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("memory_id", sa.String(length=32), sa.ForeignKey("memory_units.id"), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_memory_sources_memory_id", "memory_sources", ["memory_id"])
    op.create_index("ix_memory_sources_source", "memory_sources", ["source_type", "source_id"])

    op.create_table(
        "refactor_runs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("workflow_id", sa.String(length=128), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_refactor_runs_status", "refactor_runs", ["status"])

    op.create_table(
        "memory_operations",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("refactor_run_id", sa.String(length=32), sa.ForeignKey("refactor_runs.id"), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("source_memory_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("proposed_memory", sa.JSON(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="needs_review"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_memory_operations_refactor_run_id", "memory_operations", ["refactor_run_id"])
    op.create_index("ix_memory_operations_review_status", "memory_operations", ["review_status"])

    op.create_table(
        "memory_versions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("memory_id", sa.String(length=32), sa.ForeignKey("memory_units.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("operation_id", sa.String(length=32), sa.ForeignKey("memory_operations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("memory_id", "version", name="uq_memory_versions_memory_id_version"),
    )
    op.create_index("ix_memory_versions_memory_id", "memory_versions", ["memory_id"])

    op.create_table(
        "contradictions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("refactor_run_id", sa.String(length=32), sa.ForeignKey("refactor_runs.id"), nullable=False),
        sa.Column("memory_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("proposed_resolution", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_contradictions_refactor_run_id", "contradictions", ["refactor_run_id"])
    op.create_index("ix_contradictions_status", "contradictions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_contradictions_status", table_name="contradictions")
    op.drop_index("ix_contradictions_refactor_run_id", table_name="contradictions")
    op.drop_table("contradictions")

    op.drop_index("ix_memory_versions_memory_id", table_name="memory_versions")
    op.drop_table("memory_versions")

    op.drop_index("ix_memory_operations_review_status", table_name="memory_operations")
    op.drop_index("ix_memory_operations_refactor_run_id", table_name="memory_operations")
    op.drop_table("memory_operations")

    op.drop_index("ix_refactor_runs_status", table_name="refactor_runs")
    op.drop_table("refactor_runs")

    op.drop_index("ix_memory_sources_source", table_name="memory_sources")
    op.drop_index("ix_memory_sources_memory_id", table_name="memory_sources")
    op.drop_table("memory_sources")

    op.drop_index("ix_memory_units_status", table_name="memory_units")
    op.drop_index("ix_memory_units_kind", table_name="memory_units")
    op.drop_table("memory_units")

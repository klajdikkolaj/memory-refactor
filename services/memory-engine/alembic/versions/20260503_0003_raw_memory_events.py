"""Add raw memory events.

Revision ID: 20260503_0003
Revises: 20260503_0002
Create Date: 2026-05-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260503_0003"
down_revision: str | None = "20260503_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "raw_memory_events",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_raw_memory_events_source_type", "raw_memory_events", ["source_type"])
    op.create_index("ix_raw_memory_events_source_id", "raw_memory_events", ["source_id"])
    op.create_index("ix_raw_memory_events_processed_at", "raw_memory_events", ["processed_at"])

    op.add_column(
        "memory_sources",
        sa.Column("raw_event_id", sa.String(length=32), nullable=True),
    )
    op.create_foreign_key(
        "fk_memory_sources_raw_event_id_raw_memory_events",
        "memory_sources",
        "raw_memory_events",
        ["raw_event_id"],
        ["id"],
    )
    op.create_index("ix_memory_sources_raw_event_id", "memory_sources", ["raw_event_id"])

    op.add_column(
        "refactor_runs",
        sa.Column("input_event_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )

    op.add_column(
        "memory_operations",
        sa.Column("source_event_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )


def downgrade() -> None:
    op.drop_column("memory_operations", "source_event_ids")

    op.drop_column("refactor_runs", "input_event_ids")

    op.drop_index("ix_memory_sources_raw_event_id", table_name="memory_sources")
    op.drop_constraint(
        "fk_memory_sources_raw_event_id_raw_memory_events",
        "memory_sources",
        type_="foreignkey",
    )
    op.drop_column("memory_sources", "raw_event_id")

    op.drop_index("ix_raw_memory_events_processed_at", table_name="raw_memory_events")
    op.drop_index("ix_raw_memory_events_source_id", table_name="raw_memory_events")
    op.drop_index("ix_raw_memory_events_source_type", table_name="raw_memory_events")
    op.drop_table("raw_memory_events")

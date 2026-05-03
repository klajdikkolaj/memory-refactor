"""Add memory relationships.

Revision ID: 20260503_0005
Revises: 20260503_0004
Create Date: 2026-05-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260503_0005"
down_revision: str | None = "20260503_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_relationships",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("subject", sa.String(length=256), nullable=False),
        sa.Column("predicate", sa.String(length=128), nullable=False),
        sa.Column("object_id", sa.String(length=256), nullable=False),
        sa.Column(
            "source_memory_id",
            sa.String(length=32),
            sa.ForeignKey("memory_units.id"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from",
            name="ck_memory_relationships_valid_window",
        ),
    )
    op.create_index("ix_memory_relationships_subject", "memory_relationships", ["subject"])
    op.create_index("ix_memory_relationships_predicate", "memory_relationships", ["predicate"])
    op.create_index("ix_memory_relationships_object_id", "memory_relationships", ["object_id"])
    op.create_index(
        "ix_memory_relationships_source_memory_id",
        "memory_relationships",
        ["source_memory_id"],
    )
    op.create_index(
        "ix_memory_relationships_subject_predicate",
        "memory_relationships",
        ["subject", "predicate"],
    )
    op.create_index("ix_memory_relationships_valid_from", "memory_relationships", ["valid_from"])
    op.create_index("ix_memory_relationships_valid_until", "memory_relationships", ["valid_until"])
    op.create_index(
        "ix_memory_relationships_valid_window",
        "memory_relationships",
        ["valid_from", "valid_until"],
    )


def downgrade() -> None:
    op.drop_index("ix_memory_relationships_valid_window", table_name="memory_relationships")
    op.drop_index("ix_memory_relationships_valid_until", table_name="memory_relationships")
    op.drop_index("ix_memory_relationships_valid_from", table_name="memory_relationships")
    op.drop_index("ix_memory_relationships_subject_predicate", table_name="memory_relationships")
    op.drop_index("ix_memory_relationships_source_memory_id", table_name="memory_relationships")
    op.drop_index("ix_memory_relationships_object_id", table_name="memory_relationships")
    op.drop_index("ix_memory_relationships_predicate", table_name="memory_relationships")
    op.drop_index("ix_memory_relationships_subject", table_name="memory_relationships")
    op.drop_table("memory_relationships")

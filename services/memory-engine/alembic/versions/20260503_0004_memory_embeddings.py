"""Add memory embeddings.

Revision ID: 20260503_0004
Revises: 20260503_0003
Create Date: 2026-05-03
"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

revision: str = "20260503_0004"
down_revision: str | None = "20260503_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "memory_embeddings",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column(
            "memory_id",
            sa.String(length=32),
            sa.ForeignKey("memory_units.id"),
            nullable=False,
        ),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "memory_id",
            "embedding_model",
            "dimensions",
            name="uq_memory_embeddings_memory_model_dimensions",
        ),
    )
    op.create_index("ix_memory_embeddings_memory_id", "memory_embeddings", ["memory_id"])
    op.create_index("ix_memory_embeddings_embedding_model", "memory_embeddings", ["embedding_model"])
    op.create_index(
        "ix_memory_embeddings_model_dimensions",
        "memory_embeddings",
        ["embedding_model", "dimensions"],
    )


def downgrade() -> None:
    op.drop_index("ix_memory_embeddings_model_dimensions", table_name="memory_embeddings")
    op.drop_index("ix_memory_embeddings_embedding_model", table_name="memory_embeddings")
    op.drop_index("ix_memory_embeddings_memory_id", table_name="memory_embeddings")
    op.drop_table("memory_embeddings")

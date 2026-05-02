from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from memory_refactor.core.ids import new_id
from memory_refactor.core.models import MemoryStatus, RefactorRunStatus
from memory_refactor.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MemoryUnitRecord(TimestampMixin, Base):
    __tablename__ = "memory_units"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: new_id("mem"))
    kind: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=MemoryStatus.ACTIVE.value,
        index=True,
        nullable=False,
    )
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)

    sources: Mapped[list[MemorySourceRecord]] = relationship(
        back_populates="memory",
        cascade="all, delete-orphan",
    )
    versions: Mapped[list[MemoryVersionRecord]] = relationship(back_populates="memory")


class MemorySourceRecord(Base):
    __tablename__ = "memory_sources"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: new_id("src"))
    memory_id: Mapped[str] = mapped_column(ForeignKey("memory_units.id"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    memory: Mapped[MemoryUnitRecord] = relationship(back_populates="sources")


class RefactorRunRecord(TimestampMixin, Base):
    __tablename__ = "refactor_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: new_id("run"))
    status: Mapped[str] = mapped_column(
        String(32),
        default=RefactorRunStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    workflow_id: Mapped[str | None] = mapped_column(String(128))
    trace_id: Mapped[str | None] = mapped_column(String(128))

    operations: Mapped[list[MemoryOperationRecord]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
    contradictions: Mapped[list[ContradictionRecord]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class MemoryOperationRecord(TimestampMixin, Base):
    __tablename__ = "memory_operations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: new_id("op"))
    refactor_run_id: Mapped[str] = mapped_column(
        ForeignKey("refactor_runs.id"),
        index=True,
        nullable=False,
    )
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    source_memory_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    proposed_memory: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="needs_review", index=True)
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)

    run: Mapped[RefactorRunRecord] = relationship(back_populates="operations")
    versions: Mapped[list[MemoryVersionRecord]] = relationship(back_populates="operation")


class MemoryVersionRecord(Base):
    __tablename__ = "memory_versions"
    __table_args__ = (
        UniqueConstraint("memory_id", "version", name="uq_memory_versions_memory_id_version"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: new_id("ver"))
    memory_id: Mapped[str] = mapped_column(ForeignKey("memory_units.id"), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    operation_id: Mapped[str | None] = mapped_column(ForeignKey("memory_operations.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    memory: Mapped[MemoryUnitRecord] = relationship(back_populates="versions")
    operation: Mapped[MemoryOperationRecord | None] = relationship(back_populates="versions")


class ContradictionRecord(TimestampMixin, Base):
    __tablename__ = "contradictions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: new_id("con"))
    refactor_run_id: Mapped[str] = mapped_column(
        ForeignKey("refactor_runs.id"),
        index=True,
        nullable=False,
    )
    memory_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    proposed_resolution: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True, nullable=False)

    run: Mapped[RefactorRunRecord] = relationship(back_populates="contradictions")

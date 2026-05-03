from datetime import datetime, timezone
from enum import StrEnum
from math import isfinite
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from memory_refactor.core.ids import new_id


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryKind(StrEnum):
    PROFILE = "profile"
    FACT = "fact"
    PREFERENCE = "preference"
    GOAL = "goal"
    PROJECT = "project"
    SKILL = "skill"
    RELATIONSHIP = "relationship"
    DECISION = "decision"
    HABIT = "habit"
    CONSTRAINT = "constraint"
    OPEN_QUESTION = "open_question"
    CONTRADICTION = "contradiction"
    SUMMARY = "summary"
    OBSERVATION = "observation"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    CONFLICTED = "conflicted"


class OperationKind(StrEnum):
    CREATE_MEMORY = "create_memory"
    MERGE_MEMORIES = "merge_memories"
    SPLIT_MEMORY = "split_memory"
    SUPERSEDE_MEMORY = "supersede_memory"
    ARCHIVE_MEMORY = "archive_memory"
    MARK_CONTRADICTION = "mark_contradiction"


class RefactorRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    NEEDS_REVIEW = "needs_review"
    APPLIED = "applied"
    FAILED = "failed"


class OperationReviewStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


class RawMemoryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("evt"))
    source_type: str
    source_id: str | None = None
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    processed_at: datetime | None = None


class MemorySource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_id: str
    raw_event_id: str | None = None
    excerpt: str | None = None
    url: str | None = None
    captured_at: datetime = Field(default_factory=_now)


class MemoryUnit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("mem"))
    kind: MemoryKind
    content: str = Field(min_length=1)
    confidence: float = Field(default=0.75, ge=0, le=1)
    status: MemoryStatus = MemoryStatus.ACTIVE
    sources: list[MemorySource] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class MemoryOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("op"))
    operation: OperationKind
    source_memory_ids: list[str] = Field(default_factory=list)
    source_event_ids: list[str] = Field(default_factory=list)
    proposed_memory: MemoryUnit | None = None
    rationale: str = Field(min_length=1)
    confidence: float = Field(default=0.75, ge=0, le=1)
    requires_human_review: bool = True
    review_status: OperationReviewStatus = OperationReviewStatus.NEEDS_REVIEW
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("rev"))
    run_id: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    decision: OperationReviewStatus
    reason: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class Contradiction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("con"))
    memory_ids: list[str] = Field(min_length=2)
    summary: str = Field(min_length=1)
    confidence: float = Field(default=0.75, ge=0, le=1)
    proposed_resolution: MemoryOperation | None = None


class RefactorPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("plan"))
    run_id: str = Field(default_factory=lambda: new_id("run"))
    workflow_id: str | None = None
    trace_id: str | None = None
    status: RefactorRunStatus = RefactorRunStatus.NEEDS_REVIEW
    summary: str = Field(min_length=1)
    input_event_ids: list[str] = Field(default_factory=list)
    operations: list[MemoryOperation]
    contradictions: list[Contradiction] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)


class RefactorWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(default_factory=lambda: new_id("run"))
    raw_event_ids: list[str] = Field(min_length=1)


class MemoryVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("ver"))
    memory_id: str
    version: int = Field(ge=1)
    snapshot: MemoryUnit
    operation_id: str | None = None
    created_at: datetime = Field(default_factory=_now)


class EmbeddingVector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[float] = Field(min_length=1)

    @field_validator("values")
    @classmethod
    def validate_finite_values(cls, values: list[float]) -> list[float]:
        if any(not isfinite(value) for value in values):
            raise ValueError("embedding values must be finite")
        return values

    @property
    def dimensions(self) -> int:
        return len(self.values)


class MemoryEmbedding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("emb"))
    memory_id: str = Field(min_length=1)
    embedding_model: str = Field(min_length=1, max_length=128)
    vector: EmbeddingVector
    content_hash: str | None = Field(default=None, max_length=128)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class MemorySearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory: MemoryUnit
    distance: float = Field(ge=0)
    embedding_model: str


class MemoryRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("rel"))
    subject: str = Field(min_length=1, max_length=256)
    predicate: str = Field(min_length=1, max_length=128)
    object_id: str = Field(min_length=1, max_length=256)
    source_memory_id: str = Field(min_length=1)
    confidence: float = Field(default=0.75, ge=0, le=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    @model_validator(mode="after")
    def validate_temporal_window(self) -> "MemoryRelationship":
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until <= self.valid_from
        ):
            raise ValueError("valid_until must be after valid_from")
        return self

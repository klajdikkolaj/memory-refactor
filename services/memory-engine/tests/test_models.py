from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from memory_refactor.core.models import (
    EmbeddingVector,
    MemoryKind,
    MemoryOperation,
    MemoryRelationship,
    MemoryUnit,
    OperationKind,
    RawMemoryEvent,
)
from memory_refactor.core.operations import (
    propose_seed_refactor_plan,
    propose_seed_refactor_plan_from_raw_events,
)


def test_seed_refactor_plan_produces_typed_merge_operation() -> None:
    memories = [
        MemoryUnit(kind=MemoryKind.PREFERENCE, content="Use TypeScript for UI."),
        MemoryUnit(kind=MemoryKind.PREFERENCE, content="Use Python for AI."),
    ]

    plan = propose_seed_refactor_plan(memories)

    assert len(plan.operations) == 1
    assert isinstance(plan.operations[0], MemoryOperation)
    assert plan.operations[0].operation is OperationKind.MERGE_MEMORIES
    assert plan.operations[0].requires_human_review is True


def test_seed_raw_event_refactor_plan_produces_source_grounded_create_operation() -> None:
    events = [
        RawMemoryEvent(
            id="evt_stack",
            source_type="manual",
            content="I use Go, React, NestJS, and Vue.",
        ),
        RawMemoryEvent(
            id="evt_goal",
            source_type="manual",
            content="I am learning ML because I want to become an RL developer.",
        ),
    ]

    plan = propose_seed_refactor_plan_from_raw_events(events)
    operation = plan.operations[0]

    assert operation.operation is OperationKind.CREATE_MEMORY
    assert operation.source_event_ids == ["evt_stack", "evt_goal"]
    assert operation.source_memory_ids == []
    assert operation.proposed_memory is not None
    assert operation.proposed_memory.kind is MemoryKind.SUMMARY
    assert [source.raw_event_id for source in operation.proposed_memory.sources] == [
        "evt_stack",
        "evt_goal",
    ]


def test_embedding_vector_tracks_dimensions() -> None:
    vector = EmbeddingVector(values=[0.1, 0.2, 0.3])

    assert vector.dimensions == 3


def test_embedding_vector_rejects_non_finite_values() -> None:
    with pytest.raises(ValidationError):
        EmbeddingVector(values=[0.1, float("nan")])


def test_memory_relationship_accepts_open_temporal_window() -> None:
    relationship = MemoryRelationship(
        subject="user",
        predicate="works_on",
        object_id="memory-refactor",
        source_memory_id="mem_project",
        valid_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )

    assert relationship.valid_until is None


def test_memory_relationship_rejects_inverted_temporal_window() -> None:
    with pytest.raises(ValidationError):
        MemoryRelationship(
            subject="user",
            predicate="works_on",
            object_id="memory-refactor",
            source_memory_id="mem_project",
            valid_from=datetime(2026, 5, 2, tzinfo=timezone.utc),
            valid_until=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

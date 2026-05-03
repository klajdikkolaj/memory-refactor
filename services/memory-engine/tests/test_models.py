from memory_refactor.core.models import (
    MemoryKind,
    MemoryOperation,
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

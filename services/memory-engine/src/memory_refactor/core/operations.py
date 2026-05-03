from memory_refactor.core.models import (
    MemoryKind,
    MemoryOperation,
    MemorySource,
    MemoryUnit,
    OperationKind,
    RawMemoryEvent,
    RefactorPlan,
)


def propose_seed_refactor_plan(memories: list[MemoryUnit]) -> RefactorPlan:
    """Deterministic placeholder until the Pydantic AI agent is wired in."""
    source_ids = [memory.id for memory in memories]
    proposed_memory = MemoryUnit(
        kind=MemoryKind.PREFERENCE,
        content="Use TypeScript for product UI and Python for AI memory intelligence.",
        confidence=0.9,
        sources=[source for memory in memories for source in memory.sources],
    )

    operation = MemoryOperation(
        operation=OperationKind.MERGE_MEMORIES,
        source_memory_ids=source_ids,
        proposed_memory=proposed_memory,
        rationale=(
            "The inputs describe complementary stack preferences and should become one "
            "canonical architecture memory."
        ),
        confidence=0.9,
        requires_human_review=True,
    )

    return RefactorPlan(
        summary="Seed refactor plan with one merge operation.",
        operations=[operation],
    )


def propose_seed_refactor_plan_from_raw_events(events: list[RawMemoryEvent]) -> RefactorPlan:
    """Deterministic raw-event refactor until the Pydantic AI agent is wired in."""
    source_event_ids = [event.id for event in events]
    combined_content = " ".join(event.content.strip() for event in events)
    proposed_memory = MemoryUnit(
        kind=MemoryKind.SUMMARY,
        content=combined_content,
        confidence=0.8,
        sources=[
            MemorySource(
                source_type=event.source_type,
                source_id=event.source_id or event.id,
                raw_event_id=event.id,
                excerpt=event.content[:500],
                captured_at=event.created_at,
            )
            for event in events
        ],
        metadata={"refactor_mode": "raw_event_seed"},
    )

    operation = MemoryOperation(
        operation=OperationKind.CREATE_MEMORY,
        source_event_ids=source_event_ids,
        proposed_memory=proposed_memory,
        rationale="The raw events were consolidated into an initial clean memory candidate.",
        confidence=0.8,
        requires_human_review=True,
    )

    return RefactorPlan(
        summary="Created one clean memory candidate from raw events.",
        input_event_ids=source_event_ids,
        operations=[operation],
    )

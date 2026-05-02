from memory_refactor.core.models import (
    MemoryKind,
    MemoryOperation,
    MemoryUnit,
    OperationKind,
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

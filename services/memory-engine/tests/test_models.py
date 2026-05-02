from memory_refactor.core.models import MemoryKind, MemoryOperation, MemoryUnit, OperationKind
from memory_refactor.core.operations import propose_seed_refactor_plan


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

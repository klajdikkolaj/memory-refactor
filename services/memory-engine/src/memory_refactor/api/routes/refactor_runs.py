from fastapi import APIRouter

from memory_refactor.core.models import MemoryKind, MemorySource, MemoryUnit, RefactorPlan
from memory_refactor.core.operations import propose_seed_refactor_plan

router = APIRouter(prefix="/refactor-runs", tags=["refactor-runs"])


@router.post("/preview", response_model=RefactorPlan)
async def preview_refactor_run() -> RefactorPlan:
    seed_memories = [
        MemoryUnit(
            kind=MemoryKind.PREFERENCE,
            content="Use TypeScript for the product UI.",
            sources=[MemorySource(source_type="note", source_id="seed_ts")],
        ),
        MemoryUnit(
            kind=MemoryKind.PREFERENCE,
            content="Use Python for AI and memory intelligence.",
            sources=[MemorySource(source_type="note", source_id="seed_python")],
        ),
    ]

    return propose_seed_refactor_plan(seed_memories)

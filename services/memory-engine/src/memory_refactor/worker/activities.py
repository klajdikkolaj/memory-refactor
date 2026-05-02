from temporalio import activity

from memory_refactor.core.models import MemoryUnit, RefactorPlan
from memory_refactor.core.operations import propose_seed_refactor_plan


@activity.defn
async def create_refactor_plan(memory_payloads: list[dict]) -> dict:
    memories = [MemoryUnit.model_validate(payload) for payload in memory_payloads]
    plan: RefactorPlan = propose_seed_refactor_plan(memories)
    return plan.model_dump(mode="json")

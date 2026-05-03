from __future__ import annotations

from typing import Any, Protocol

from memory_refactor.core.models import MemoryOperation, MemoryUnit, RefactorPlan, RefactorRunStatus
from memory_refactor.core.operations import propose_seed_refactor_plan
from memory_refactor.core.settings import Settings, get_settings


REFACTOR_AGENT_INSTRUCTIONS = """You are the Memory Refactor agent.

Return only a schema-valid RefactorPlan. Propose typed MemoryOperation objects; do not mutate
canonical memory directly. Every operation must cite source_memory_ids from the provided inputs,
include a concise rationale, set requires_human_review to true, and keep contradictions reviewable.
Prefer small, source-grounded operations over broad summaries.
"""


class AgentRunResultLike(Protocol):
    output: Any


class RefactorAgentRunner(Protocol):
    async def run(self, prompt: str) -> AgentRunResultLike:
        ...


class InvalidAgentPlanError(ValueError):
    pass


class DeterministicRefactorAgent:
    async def propose_plan(self, memories: list[MemoryUnit]) -> RefactorPlan:
        return propose_seed_refactor_plan(memories)


class PydanticAIRunner:
    def __init__(self, *, model_name: str, retries: int = 1) -> None:
        from pydantic_ai import Agent

        self._agent = Agent(
            model_name,
            output_type=RefactorPlan,
            instructions=REFACTOR_AGENT_INSTRUCTIONS,
            retries=retries,
        )

    async def run(self, prompt: str) -> AgentRunResultLike:
        return await self._agent.run(prompt)


class PydanticAIRefactorAgent:
    def __init__(
        self,
        runner: RefactorAgentRunner,
        *,
        fallback: DeterministicRefactorAgent | None = None,
    ) -> None:
        self._runner = runner
        self._fallback = fallback

    async def propose_plan(self, memories: list[MemoryUnit]) -> RefactorPlan:
        prompt = build_refactor_prompt(memories)
        try:
            result = await self._runner.run(prompt)
            plan = RefactorPlan.model_validate(result.output)
            return validate_refactor_plan_output(plan, memories)
        except Exception:
            if self._fallback is None:
                raise
            return await self._fallback.propose_plan(memories)


def build_refactor_prompt(memories: list[MemoryUnit]) -> str:
    memory_sections = []
    for memory in memories:
        source_lines = [
            (
                f"- source_type={source.source_type}; source_id={source.source_id}; "
                f"raw_event_id={source.raw_event_id or 'none'}; excerpt={source.excerpt or 'none'}"
            )
            for source in memory.sources
        ]
        memory_sections.append(
            "\n".join(
                [
                    f"Memory {memory.id}",
                    f"kind: {memory.kind.value}",
                    f"status: {memory.status.value}",
                    f"content: {memory.content}",
                    f"confidence: {memory.confidence}",
                    "sources:",
                    *source_lines,
                ]
            )
        )

    return "\n\n".join(
        [
            "Propose a Memory PR from these related memories.",
            "Allowed operation kinds: create_memory, merge_memories, split_memory, "
            "supersede_memory, archive_memory, mark_contradiction.",
            "Constraints: source_memory_ids must come from the provided Memory ids; every "
            "operation needs rationale, confidence, and requires_human_review=true.",
            "Provided memories:",
            "\n\n".join(memory_sections),
        ]
    )


def validate_refactor_plan_output(plan: RefactorPlan, memories: list[MemoryUnit]) -> RefactorPlan:
    known_memory_ids = {memory.id for memory in memories}
    operations = [
        _validate_operation_source_grounding(operation, known_memory_ids)
        for operation in plan.operations
    ]
    return plan.model_copy(
        update={
            "status": RefactorRunStatus.NEEDS_REVIEW,
            "input_event_ids": [],
            "operations": operations,
        }
    )


def _validate_operation_source_grounding(
    operation: MemoryOperation,
    known_memory_ids: set[str],
) -> MemoryOperation:
    if not operation.source_memory_ids:
        raise InvalidAgentPlanError("agent operation must cite source_memory_ids")

    unknown_memory_ids = set(operation.source_memory_ids) - known_memory_ids
    if unknown_memory_ids:
        unknown = ", ".join(sorted(unknown_memory_ids))
        raise InvalidAgentPlanError(f"agent operation cited unknown memories: {unknown}")

    return operation.model_copy(update={"requires_human_review": True})


def build_refactor_agent(settings: Settings | None = None) -> DeterministicRefactorAgent | PydanticAIRefactorAgent:
    settings = settings or get_settings()
    fallback = DeterministicRefactorAgent()

    if not settings.refactor_agent_model:
        return fallback

    try:
        runner = PydanticAIRunner(
            model_name=settings.refactor_agent_model,
            retries=settings.refactor_agent_retries,
        )
    except Exception:
        return fallback

    return PydanticAIRefactorAgent(runner, fallback=fallback)

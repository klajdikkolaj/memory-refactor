from dataclasses import dataclass

import pytest

from memory_refactor.core.agents import (
    DeterministicRefactorAgent,
    PydanticAIRefactorAgent,
    build_refactor_agent,
    build_refactor_prompt,
)
from memory_refactor.core.models import (
    MemoryKind,
    MemoryOperation,
    MemorySource,
    MemoryUnit,
    OperationKind,
    RefactorPlan,
    RefactorRunStatus,
)
from memory_refactor.core.settings import Settings


@dataclass
class FakeRunResult:
    output: RefactorPlan


class FakeRunner:
    def __init__(self, output: RefactorPlan) -> None:
        self.output = output
        self.prompts: list[str] = []

    async def run(self, prompt: str) -> FakeRunResult:
        self.prompts.append(prompt)
        return FakeRunResult(output=self.output)


def _memory(memory_id: str, content: str) -> MemoryUnit:
    return MemoryUnit(
        id=memory_id,
        kind=MemoryKind.PREFERENCE,
        content=content,
        sources=[
            MemorySource(
                source_type="note",
                source_id=f"source_{memory_id}",
                excerpt=content,
            )
        ],
    )


def _plan(source_memory_ids: list[str]) -> RefactorPlan:
    return RefactorPlan(
        summary="Merge related preferences.",
        status=RefactorRunStatus.APPLIED,
        operations=[
            MemoryOperation(
                operation=OperationKind.MERGE_MEMORIES,
                source_memory_ids=source_memory_ids,
                proposed_memory=MemoryUnit(
                    kind=MemoryKind.PREFERENCE,
                    content="Use TypeScript for UI and Python for AI memory intelligence.",
                ),
                rationale="The sources describe compatible stack preferences.",
                requires_human_review=False,
            )
        ],
    )


def test_build_refactor_prompt_includes_source_evidence_and_constraints() -> None:
    prompt = build_refactor_prompt(
        [
            _memory("mem_ts", "Use TypeScript for UI."),
            _memory("mem_py", "Use Python for AI."),
        ]
    )

    assert "Memory mem_ts" in prompt
    assert "Use TypeScript for UI." in prompt
    assert "source_memory_ids must come from the provided Memory ids" in prompt
    assert "requires_human_review=true" in prompt


@pytest.mark.asyncio
async def test_pydantic_ai_refactor_agent_accepts_schema_valid_source_grounded_plan() -> None:
    memories = [
        _memory("mem_ts", "Use TypeScript for UI."),
        _memory("mem_py", "Use Python for AI."),
    ]
    runner = FakeRunner(_plan(["mem_ts", "mem_py"]))
    agent = PydanticAIRefactorAgent(runner, fallback=DeterministicRefactorAgent())

    plan = await agent.propose_plan(memories)

    assert runner.prompts
    assert plan.status is RefactorRunStatus.NEEDS_REVIEW
    assert plan.input_event_ids == []
    assert plan.operations[0].source_memory_ids == ["mem_ts", "mem_py"]
    assert plan.operations[0].requires_human_review is True


@pytest.mark.asyncio
async def test_pydantic_ai_refactor_agent_falls_back_on_ungrounded_output() -> None:
    memories = [
        _memory("mem_ts", "Use TypeScript for UI."),
        _memory("mem_py", "Use Python for AI."),
    ]
    runner = FakeRunner(_plan(["mem_unknown"]))
    agent = PydanticAIRefactorAgent(runner, fallback=DeterministicRefactorAgent())

    plan = await agent.propose_plan(memories)

    assert plan.summary == "Seed refactor plan with one merge operation."
    assert plan.operations[0].source_memory_ids == ["mem_ts", "mem_py"]


def test_build_refactor_agent_returns_deterministic_fallback_without_model() -> None:
    agent = build_refactor_agent(Settings(refactor_agent_model=None))

    assert isinstance(agent, DeterministicRefactorAgent)

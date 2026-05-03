from datetime import datetime, timezone

from memory_refactor.core.models import (
    Contradiction,
    MemoryKind,
    MemoryOperation,
    MemorySource,
    MemoryUnit,
    OperationKind,
    OperationReviewStatus,
    RefactorPlan,
    RefactorRunStatus,
    ReviewDecision,
)
from memory_refactor.db.repositories.refactor_runs import (
    refactor_plan_from_record,
    refactor_plan_to_record,
    review_decision_from_record,
    review_decision_to_record,
)


def test_refactor_plan_record_mapping_round_trips_contract_fields() -> None:
    captured_at = datetime(2026, 5, 3, tzinfo=timezone.utc)
    proposed_memory = MemoryUnit(
        id="mem_proposed",
        kind=MemoryKind.PREFERENCE,
        content="Use Python for memory intelligence.",
        confidence=0.88,
        sources=[
            MemorySource(
                source_type="note",
                source_id="seed_python",
                raw_event_id="evt_python",
                excerpt="Python for AI memory intelligence.",
                captured_at=captured_at,
            )
        ],
        metadata={"topic": "stack"},
        created_at=captured_at,
        updated_at=captured_at,
    )
    operation = MemoryOperation(
        id="op_merge",
        operation=OperationKind.MERGE_MEMORIES,
        source_memory_ids=["mem_ts", "mem_python"],
        source_event_ids=["evt_ts", "evt_python"],
        proposed_memory=proposed_memory,
        rationale="The source memories describe complementary stack choices.",
        confidence=0.9,
        review_status=OperationReviewStatus.APPROVED,
        metadata={"planner": "seed"},
    )
    contradiction = Contradiction(
        id="con_stack",
        memory_ids=["mem_old", "mem_new"],
        summary="The stack preference changed over time.",
        confidence=0.8,
        proposed_resolution=operation,
    )
    plan = RefactorPlan(
        id="plan_stack",
        run_id="run_stack",
        workflow_id="workflow_stack",
        trace_id="trace_stack",
        status=RefactorRunStatus.NEEDS_REVIEW,
        summary="Stack refactor proposal.",
        input_event_ids=["evt_ts", "evt_python"],
        operations=[operation],
        contradictions=[contradiction],
        created_at=captured_at,
    )

    record = refactor_plan_to_record(plan)
    mapped = refactor_plan_from_record(record)

    assert record.id == "run_stack"
    assert record.plan_id == "plan_stack"
    assert record.workflow_id == "workflow_stack"
    assert record.trace_id == "trace_stack"
    assert record.input_event_ids == ["evt_ts", "evt_python"]
    assert record.operations[0].position == 0
    assert record.operations[0].source_event_ids == ["evt_ts", "evt_python"]
    assert record.operations[0].review_status == "approved"
    assert mapped.id == "plan_stack"
    assert mapped.run_id == "run_stack"
    assert mapped.workflow_id == "workflow_stack"
    assert mapped.trace_id == "trace_stack"
    assert mapped.input_event_ids == ["evt_ts", "evt_python"]
    assert mapped.status is RefactorRunStatus.NEEDS_REVIEW
    assert mapped.operations[0].operation is OperationKind.MERGE_MEMORIES
    assert mapped.operations[0].source_event_ids == ["evt_ts", "evt_python"]
    assert mapped.operations[0].review_status is OperationReviewStatus.APPROVED
    assert mapped.operations[0].proposed_memory == proposed_memory
    assert mapped.contradictions[0].proposed_resolution == operation


def test_review_decision_record_mapping_round_trips_contract_fields() -> None:
    captured_at = datetime(2026, 5, 3, tzinfo=timezone.utc)
    decision = ReviewDecision(
        id="rev_1",
        run_id="run_stack",
        operation_id="op_merge",
        decision=OperationReviewStatus.REJECTED,
        reason="The proposed memory overstates the source.",
        metadata={"surface": "api"},
        created_at=captured_at,
    )

    record = review_decision_to_record(decision)
    mapped = review_decision_from_record(record)

    assert record.refactor_run_id == "run_stack"
    assert record.operation_id == "op_merge"
    assert record.decision == "rejected"
    assert mapped == decision

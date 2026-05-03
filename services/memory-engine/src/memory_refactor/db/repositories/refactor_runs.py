from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from memory_refactor.core.models import (
    Contradiction,
    MemoryOperation,
    OperationKind,
    OperationReviewStatus,
    MemoryUnit,
    RefactorPlan,
    RefactorRunStatus,
    ReviewDecision,
)
from memory_refactor.db.repositories.memory_units import memory_unit_to_record
from memory_refactor.db.tables import (
    ContradictionRecord,
    MemoryOperationRecord,
    MemoryUnitRecord,
    MemoryVersionRecord,
    RefactorRunRecord,
    RawMemoryEventRecord,
    ReviewDecisionRecord,
)


@dataclass(frozen=True)
class ApplyMemoryOperationResult:
    operation: MemoryOperation
    memory: MemoryUnit


class ApplyMemoryOperationError(Exception):
    message = "Unable to apply approved memory operation"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)


class RefactorRunNotFoundError(ApplyMemoryOperationError):
    message = "Refactor run not found"


class RefactorRunNotReviewableError(ApplyMemoryOperationError):
    message = "Refactor run is not awaiting review"


class MemoryOperationNotFoundError(ApplyMemoryOperationError):
    message = "Memory operation not found"


class MemoryOperationNotApprovedError(ApplyMemoryOperationError):
    message = "Memory operation is not approved"


class UnsupportedApprovedMemoryOperationError(ApplyMemoryOperationError):
    message = "Only approved create_memory operations can be applied in the MVP"


class InvalidApprovedMemoryOperationError(ApplyMemoryOperationError):
    message = "Approved memory operation is missing a proposed memory"


class MissingSourceEvidenceError(ApplyMemoryOperationError):
    message = "Approved memory operation references missing source evidence"


class ProposedMemoryAlreadyExistsError(ApplyMemoryOperationError):
    message = "Proposed memory already exists"


def _operation_from_record(record: MemoryOperationRecord) -> MemoryOperation:
    return MemoryOperation(
        id=record.id,
        operation=record.operation,
        source_memory_ids=record.source_memory_ids,
        source_event_ids=record.source_event_ids,
        proposed_memory=(
            MemoryUnit.model_validate(record.proposed_memory)
            if record.proposed_memory is not None
            else None
        ),
        rationale=record.rationale,
        confidence=record.confidence,
        requires_human_review=record.requires_human_review,
        review_status=record.review_status or OperationReviewStatus.NEEDS_REVIEW,
        metadata=record.extra,
    )


def _operation_to_record(operation: MemoryOperation, *, run_id: str, position: int) -> MemoryOperationRecord:
    return MemoryOperationRecord(
        id=operation.id,
        refactor_run_id=run_id,
        operation=operation.operation.value,
        position=position,
        source_memory_ids=operation.source_memory_ids,
        source_event_ids=operation.source_event_ids,
        proposed_memory=(
            operation.proposed_memory.model_dump(mode="json")
            if operation.proposed_memory is not None
            else None
        ),
        rationale=operation.rationale,
        confidence=operation.confidence,
        requires_human_review=operation.requires_human_review,
        review_status=operation.review_status.value,
        extra=operation.metadata,
    )


def _contradiction_from_record(record: ContradictionRecord) -> Contradiction:
    return Contradiction(
        id=record.id,
        memory_ids=record.memory_ids,
        summary=record.summary,
        confidence=record.confidence,
        proposed_resolution=(
            MemoryOperation.model_validate(record.proposed_resolution)
            if record.proposed_resolution is not None
            else None
        ),
    )


def _contradiction_to_record(contradiction: Contradiction, *, run_id: str) -> ContradictionRecord:
    return ContradictionRecord(
        id=contradiction.id,
        refactor_run_id=run_id,
        memory_ids=contradiction.memory_ids,
        summary=contradiction.summary,
        confidence=contradiction.confidence,
        proposed_resolution=(
            contradiction.proposed_resolution.model_dump(mode="json")
            if contradiction.proposed_resolution is not None
            else None
        ),
    )


def review_decision_from_record(record: ReviewDecisionRecord) -> ReviewDecision:
    return ReviewDecision(
        id=record.id,
        run_id=record.refactor_run_id,
        operation_id=record.operation_id,
        decision=record.decision,
        reason=record.reason,
        metadata=record.extra,
        created_at=record.created_at,
    )


def review_decision_to_record(decision: ReviewDecision) -> ReviewDecisionRecord:
    return ReviewDecisionRecord(
        id=decision.id,
        refactor_run_id=decision.run_id,
        operation_id=decision.operation_id,
        decision=decision.decision.value,
        reason=decision.reason,
        extra=decision.metadata,
        created_at=decision.created_at,
    )


def refactor_plan_from_record(record: RefactorRunRecord) -> RefactorPlan:
    operations = sorted(record.operations, key=lambda operation: operation.position)

    return RefactorPlan(
        id=record.plan_id,
        run_id=record.id,
        workflow_id=record.workflow_id,
        trace_id=record.trace_id,
        status=record.status,
        summary=record.summary,
        input_event_ids=record.input_event_ids,
        operations=[_operation_from_record(operation) for operation in operations],
        contradictions=[
            _contradiction_from_record(contradiction) for contradiction in record.contradictions
        ],
        created_at=record.created_at,
    )


def refactor_plan_to_record(plan: RefactorPlan) -> RefactorRunRecord:
    return RefactorRunRecord(
        id=plan.run_id,
        plan_id=plan.id,
        workflow_id=plan.workflow_id,
        trace_id=plan.trace_id,
        status=plan.status.value,
        summary=plan.summary,
        input_event_ids=plan.input_event_ids,
        created_at=plan.created_at,
        updated_at=plan.created_at,
        operations=[
            _operation_to_record(operation, run_id=plan.run_id, position=position)
            for position, operation in enumerate(plan.operations)
        ],
        contradictions=[
            _contradiction_to_record(contradiction, run_id=plan.run_id)
            for contradiction in plan.contradictions
        ],
    )


def _refactor_plan_load_options():
    return (
        selectinload(RefactorRunRecord.operations),
        selectinload(RefactorRunRecord.contradictions),
    )


async def get_refactor_plan(session: AsyncSession, run_id: str) -> RefactorPlan | None:
    statement = (
        select(RefactorRunRecord)
        .options(*_refactor_plan_load_options())
        .where(RefactorRunRecord.id == run_id)
    )
    result = await session.scalars(statement)
    record = result.one_or_none()

    if record is None:
        return None

    return refactor_plan_from_record(record)


async def list_refactor_plans(
    session: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[RefactorPlan]:
    statement = (
        select(RefactorRunRecord)
        .options(*_refactor_plan_load_options())
        .order_by(RefactorRunRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.scalars(statement)
    return [refactor_plan_from_record(record) for record in result]


async def create_refactor_plan(session: AsyncSession, plan: RefactorPlan) -> RefactorPlan:
    record = refactor_plan_to_record(plan)
    async with session.begin():
        session.add(record)

    created = await get_refactor_plan(session, plan.run_id)
    if created is None:
        raise RuntimeError(f"Created refactor run {plan.run_id} could not be loaded")

    return created


async def complete_refactor_plan(session: AsyncSession, plan: RefactorPlan) -> RefactorPlan:
    async with session.begin():
        result = await session.scalars(
            select(RefactorRunRecord)
            .options(*_refactor_plan_load_options())
            .where(RefactorRunRecord.id == plan.run_id)
        )
        record = result.one_or_none()

        if record is None:
            record = refactor_plan_to_record(plan)
            session.add(record)
        else:
            record.plan_id = plan.id
            record.status = plan.status.value
            record.summary = plan.summary
            record.input_event_ids = plan.input_event_ids
            record.operations = [
                _operation_to_record(operation, run_id=plan.run_id, position=position)
                for position, operation in enumerate(plan.operations)
            ]
            record.contradictions = [
                _contradiction_to_record(contradiction, run_id=plan.run_id)
                for contradiction in plan.contradictions
            ]

    completed = await get_refactor_plan(session, plan.run_id)
    if completed is None:
        raise RuntimeError(f"Completed refactor run {plan.run_id} could not be loaded")

    return completed


async def complete_refactor_plan_and_mark_events_processed(
    session: AsyncSession,
    plan: RefactorPlan,
    event_ids: list[str],
) -> RefactorPlan:
    processed_at = datetime.now(timezone.utc)
    async with session.begin():
        result = await session.scalars(
            select(RefactorRunRecord)
            .options(*_refactor_plan_load_options())
            .where(RefactorRunRecord.id == plan.run_id)
        )
        record = result.one_or_none()

        if record is None:
            record = refactor_plan_to_record(plan)
            session.add(record)
        else:
            record.plan_id = plan.id
            record.status = plan.status.value
            record.summary = plan.summary
            record.input_event_ids = plan.input_event_ids
            record.operations = [
                _operation_to_record(operation, run_id=plan.run_id, position=position)
                for position, operation in enumerate(plan.operations)
            ]
            record.contradictions = [
                _contradiction_to_record(contradiction, run_id=plan.run_id)
                for contradiction in plan.contradictions
            ]

        await session.execute(
            update(RawMemoryEventRecord)
            .where(RawMemoryEventRecord.id.in_(event_ids))
            .values(processed_at=processed_at)
        )

    completed = await get_refactor_plan(session, plan.run_id)
    if completed is None:
        raise RuntimeError(f"Completed refactor run {plan.run_id} could not be loaded")

    return completed


async def create_refactor_run_shell(
    session: AsyncSession,
    *,
    run_id: str,
    workflow_id: str,
    summary: str,
    input_event_ids: list[str] | None = None,
    status: RefactorRunStatus = RefactorRunStatus.PENDING,
    trace_id: str | None = None,
) -> RefactorPlan:
    record = RefactorRunRecord(
        id=run_id,
        status=status.value,
        summary=summary,
        workflow_id=workflow_id,
        trace_id=trace_id,
        input_event_ids=input_event_ids or [],
        operations=[],
        contradictions=[],
    )
    async with session.begin():
        session.add(record)
        await session.flush()
        await session.refresh(record)

    return RefactorPlan(
        id=record.plan_id,
        run_id=record.id,
        workflow_id=record.workflow_id,
        trace_id=record.trace_id,
        status=record.status,
        summary=record.summary,
        input_event_ids=record.input_event_ids,
        operations=[],
        contradictions=[],
        created_at=record.created_at,
    )


async def update_refactor_run_status(
    session: AsyncSession,
    run_id: str,
    status: RefactorRunStatus,
    *,
    workflow_id: str | None = None,
    trace_id: str | None = None,
) -> RefactorPlan | None:
    async with session.begin():
        result = await session.scalars(
            select(RefactorRunRecord).where(RefactorRunRecord.id == run_id)
        )
        record = result.one_or_none()

        if record is None:
            return None

        record.status = status.value
        if workflow_id is not None:
            record.workflow_id = workflow_id
        if trace_id is not None:
            record.trace_id = trace_id

    return await get_refactor_plan(session, run_id)


async def update_memory_operation_review_status(
    session: AsyncSession,
    *,
    run_id: str,
    operation_id: str,
    review_status: OperationReviewStatus,
    reason: str | None = None,
) -> MemoryOperation | None:
    async with session.begin():
        result = await session.scalars(
            select(MemoryOperationRecord).where(
                MemoryOperationRecord.refactor_run_id == run_id,
                MemoryOperationRecord.id == operation_id,
            )
        )
        record = result.one_or_none()

        if record is None:
            return None

        record.review_status = review_status.value
        session.add(
            review_decision_to_record(
                ReviewDecision(
                    run_id=run_id,
                    operation_id=operation_id,
                    decision=review_status,
                    reason=reason,
                )
            )
        )
        await session.flush()

        return _operation_from_record(record)


async def list_review_decisions(
    session: AsyncSession,
    *,
    run_id: str | None = None,
    operation_id: str | None = None,
) -> list[ReviewDecision]:
    statement = select(ReviewDecisionRecord).order_by(ReviewDecisionRecord.created_at.asc())

    if run_id is not None:
        statement = statement.where(ReviewDecisionRecord.refactor_run_id == run_id)
    if operation_id is not None:
        statement = statement.where(ReviewDecisionRecord.operation_id == operation_id)

    result = await session.scalars(statement)
    return [review_decision_from_record(record) for record in result]


async def apply_approved_create_memory_operation(
    session: AsyncSession,
    *,
    run_id: str,
    operation_id: str,
) -> ApplyMemoryOperationResult:
    async with session.begin():
        result = await session.scalars(
            select(RefactorRunRecord)
            .options(*_refactor_plan_load_options())
            .where(RefactorRunRecord.id == run_id)
            .with_for_update()
        )
        run_record = result.one_or_none()

        if run_record is None:
            raise RefactorRunNotFoundError()

        if run_record.status != RefactorRunStatus.NEEDS_REVIEW.value:
            raise RefactorRunNotReviewableError()

        result = await session.scalars(
            select(MemoryOperationRecord)
            .where(
                MemoryOperationRecord.refactor_run_id == run_id,
                MemoryOperationRecord.id == operation_id,
            )
            .with_for_update()
        )
        operation_record = result.one_or_none()

        if operation_record is None:
            raise MemoryOperationNotFoundError()

        if operation_record.review_status != OperationReviewStatus.APPROVED.value:
            raise MemoryOperationNotApprovedError()

        if operation_record.operation != OperationKind.CREATE_MEMORY.value:
            raise UnsupportedApprovedMemoryOperationError()

        proposed_memory = _proposed_memory_for_approved_operation(operation_record)
        await _validate_source_evidence(session, operation_record, proposed_memory)
        await _validate_proposed_memory_does_not_exist(session, proposed_memory)

        session.add(memory_unit_to_record(proposed_memory))
        session.add(
            MemoryVersionRecord(
                memory_id=proposed_memory.id,
                version=1,
                snapshot=proposed_memory.model_dump(mode="json"),
                operation_id=operation_record.id,
            )
        )
        operation_record.review_status = OperationReviewStatus.APPLIED.value

        operations = sorted(run_record.operations, key=lambda operation: operation.position)
        if all(
            operation.review_status
            in {OperationReviewStatus.APPLIED.value, OperationReviewStatus.REJECTED.value}
            for operation in operations
        ):
            run_record.status = RefactorRunStatus.APPLIED.value

        await session.flush()

    operation = await get_memory_operation(session, run_id=run_id, operation_id=operation_id)
    if operation is None:
        raise RuntimeError(f"Applied memory operation {operation_id} could not be loaded")

    return ApplyMemoryOperationResult(
        operation=operation,
        memory=proposed_memory,
    )


async def get_memory_operation(
    session: AsyncSession,
    *,
    run_id: str,
    operation_id: str,
) -> MemoryOperation | None:
    result = await session.scalars(
        select(MemoryOperationRecord).where(
            MemoryOperationRecord.refactor_run_id == run_id,
            MemoryOperationRecord.id == operation_id,
        )
    )
    record = result.one_or_none()

    if record is None:
        return None

    return _operation_from_record(record)


def _proposed_memory_for_approved_operation(operation: MemoryOperationRecord) -> MemoryUnit:
    if operation.proposed_memory is None:
        raise InvalidApprovedMemoryOperationError()

    return MemoryUnit.model_validate(operation.proposed_memory)


async def _validate_source_evidence(
    session: AsyncSession,
    operation: MemoryOperationRecord,
    memory: MemoryUnit,
) -> None:
    source_event_ids = set(operation.source_event_ids)
    source_event_ids.update(
        source.raw_event_id for source in memory.sources if source.raw_event_id is not None
    )

    if not source_event_ids:
        raise MissingSourceEvidenceError("Approved create_memory operation needs source events")

    existing_source_event_ids = set(
        await session.scalars(
            select(RawMemoryEventRecord.id).where(RawMemoryEventRecord.id.in_(source_event_ids))
        )
    )
    missing_source_event_ids = sorted(source_event_ids - existing_source_event_ids)
    if missing_source_event_ids:
        raise MissingSourceEvidenceError(
            f"Source evidence not found: {', '.join(missing_source_event_ids)}"
        )


async def _validate_proposed_memory_does_not_exist(
    session: AsyncSession,
    memory: MemoryUnit,
) -> None:
    existing_memory_id = await session.scalar(
        select(MemoryUnitRecord.id).where(MemoryUnitRecord.id == memory.id)
    )
    if existing_memory_id is not None:
        raise ProposedMemoryAlreadyExistsError(f"Proposed memory already exists: {memory.id}")

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from memory_refactor.core.models import (
    Contradiction,
    MemoryOperation,
    MemoryUnit,
    RefactorPlan,
    RefactorRunStatus,
)
from memory_refactor.db.tables import (
    ContradictionRecord,
    MemoryOperationRecord,
    RefactorRunRecord,
    RawMemoryEventRecord,
)


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


def refactor_plan_from_record(record: RefactorRunRecord) -> RefactorPlan:
    operations = sorted(record.operations, key=lambda operation: operation.position)

    return RefactorPlan(
        id=record.plan_id,
        run_id=record.id,
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
) -> RefactorPlan:
    record = RefactorRunRecord(
        id=run_id,
        status=status.value,
        summary=summary,
        workflow_id=workflow_id,
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

    return await get_refactor_plan(session, run_id)

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from memory_refactor.core.ids import new_id
from memory_refactor.core.models import (
    MemoryKind,
    MemoryOperation,
    MemorySource,
    MemoryUnit,
    OperationReviewStatus,
    RefactorPlan,
    RefactorRunStatus,
)
from memory_refactor.core.operations import propose_seed_refactor_plan
from memory_refactor.db.repositories.raw_memory_events import list_raw_memory_events_by_ids
from memory_refactor.db.repositories.refactor_runs import (
    InvalidApprovedMemoryOperationError,
    MemoryOperationNotApprovedError,
    MemoryOperationNotFoundError,
    MissingSourceEvidenceError,
    ProposedMemoryAlreadyExistsError,
    RefactorRunNotFoundError,
    RefactorRunNotReviewableError,
    UnsupportedApprovedMemoryOperationError,
    apply_approved_create_memory_operation,
    create_refactor_run_shell,
    create_refactor_plan,
    get_refactor_plan,
    list_refactor_plans,
    update_memory_operation_review_status,
    update_refactor_run_status,
)
from memory_refactor.db.session import get_async_session
from memory_refactor.worker.starter import (
    RefactorWorkflowStarter,
    build_refactor_workflow_id,
    get_refactor_workflow_starter,
)

router = APIRouter(prefix="/refactor-runs", tags=["refactor-runs"])


def _seed_memories() -> list[MemoryUnit]:
    return [
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


class StartRefactorRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_event_ids: list[str] = Field(min_length=1)


class StartRefactorRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow_id: str
    temporal_run_id: str | None = None
    status: RefactorRunStatus


class ReviewOperationDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewMemoryOperationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: ReviewOperationDecision


class ApplyMemoryOperationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: MemoryOperation
    memory: MemoryUnit


@router.get("", response_model=list[RefactorPlan])
async def list_refactor_runs(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> list[RefactorPlan]:
    return await list_refactor_plans(session, limit=limit, offset=offset)


@router.post("", response_model=StartRefactorRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_refactor_run(
    request: StartRefactorRunRequest = Body(...),
    session: AsyncSession = Depends(get_async_session),
    workflow_starter: RefactorWorkflowStarter = Depends(get_refactor_workflow_starter),
) -> StartRefactorRunResponse:
    return await start_refactor_run_from_raw_events(
        raw_event_ids=request.raw_event_ids,
        session=session,
        workflow_starter=workflow_starter,
    )


async def start_refactor_run_from_raw_events(
    *,
    raw_event_ids: list[str],
    session: AsyncSession,
    workflow_starter: RefactorWorkflowStarter,
) -> StartRefactorRunResponse:
    events = await list_raw_memory_events_by_ids(session, raw_event_ids)
    found_event_ids = {event.id for event in events}
    missing_event_ids = [
        event_id for event_id in raw_event_ids if event_id not in found_event_ids
    ]
    if missing_event_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raw memory events not found: {', '.join(missing_event_ids)}",
        )
    await session.rollback()

    run_id = new_id("run")
    workflow_id = build_refactor_workflow_id(run_id)

    await create_refactor_run_shell(
        session,
        run_id=run_id,
        workflow_id=workflow_id,
        summary="Temporal refactor workflow is queued.",
        input_event_ids=raw_event_ids,
        status=RefactorRunStatus.PENDING,
    )

    try:
        workflow_start = await workflow_starter.start(
            run_id=run_id,
            workflow_id=workflow_id,
            raw_event_ids=raw_event_ids,
        )
    except Exception as exc:
        await update_refactor_run_status(session, run_id, RefactorRunStatus.FAILED)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal workflow start failed",
        ) from exc

    await update_refactor_run_status(
        session,
        run_id,
        RefactorRunStatus.RUNNING,
        workflow_id=workflow_start.workflow_id,
    )

    return StartRefactorRunResponse(
        run_id=run_id,
        workflow_id=workflow_start.workflow_id,
        temporal_run_id=workflow_start.temporal_run_id,
        status=RefactorRunStatus.RUNNING,
    )


@router.post("/preview", response_model=RefactorPlan, status_code=status.HTTP_201_CREATED)
async def preview_refactor_run(
    session: AsyncSession = Depends(get_async_session),
) -> RefactorPlan:
    plan = propose_seed_refactor_plan(_seed_memories())
    return await create_refactor_plan(session, plan)


@router.patch(
    "/{run_id}/operations/{operation_id}/review",
    response_model=MemoryOperation,
)
async def review_memory_operation(
    run_id: str,
    operation_id: str,
    request: ReviewMemoryOperationRequest = Body(...),
    session: AsyncSession = Depends(get_async_session),
) -> MemoryOperation:
    plan = await get_refactor_plan(session, run_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refactor run not found")

    if plan.status != RefactorRunStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Refactor run is not awaiting review",
        )

    if not any(operation.id == operation_id for operation in plan.operations):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory operation not found",
        )

    await session.rollback()
    operation = await update_memory_operation_review_status(
        session,
        run_id=run_id,
        operation_id=operation_id,
        review_status=OperationReviewStatus(request.decision.value),
    )
    if operation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory operation not found",
        )

    return operation


@router.post(
    "/{run_id}/operations/{operation_id}/apply",
    response_model=ApplyMemoryOperationResponse,
)
async def apply_approved_memory_operation(
    run_id: str,
    operation_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> ApplyMemoryOperationResponse:
    try:
        result = await apply_approved_create_memory_operation(
            session,
            run_id=run_id,
            operation_id=operation_id,
        )
    except (MemoryOperationNotFoundError, RefactorRunNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        MemoryOperationNotApprovedError,
        ProposedMemoryAlreadyExistsError,
        RefactorRunNotReviewableError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (
        InvalidApprovedMemoryOperationError,
        MissingSourceEvidenceError,
        UnsupportedApprovedMemoryOperationError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ApplyMemoryOperationResponse(
        operation=result.operation,
        memory=result.memory,
    )


@router.get("/{run_id}", response_model=RefactorPlan)
async def get_refactor_run(
    run_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> RefactorPlan:
    plan = await get_refactor_plan(session, run_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refactor run not found")

    return plan

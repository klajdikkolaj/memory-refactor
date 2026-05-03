from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from memory_refactor.api.routes.refactor_runs import start_refactor_run_from_raw_events
from memory_refactor.core.models import RawMemoryEvent, RefactorRunStatus
from memory_refactor.core.raw_batches import EmptyManualBatchError, build_manual_batch_events
from memory_refactor.db.repositories.raw_memory_events import (
    create_raw_memory_events,
    create_raw_memory_event,
    list_raw_memory_events,
)
from memory_refactor.db.session import get_async_session
from memory_refactor.worker.starter import (
    RefactorWorkflowStarter,
    get_refactor_workflow_starter,
)

router = APIRouter(prefix="/raw-memory-events", tags=["raw-memory-events"])


class CreateRawMemoryEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    source_type: str
    source_id: str | None = None
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateManualRawMemoryBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)
    source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateManualRawMemoryBatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    raw_event_ids: list[str]
    run_id: str
    workflow_id: str
    temporal_run_id: str | None = None
    status: RefactorRunStatus


@router.post(
    "/manual-batches",
    response_model=CreateManualRawMemoryBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_manual_batch(
    request: CreateManualRawMemoryBatchRequest,
    session: AsyncSession = Depends(get_async_session),
    workflow_starter: RefactorWorkflowStarter = Depends(get_refactor_workflow_starter),
) -> CreateManualRawMemoryBatchResponse:
    try:
        events = build_manual_batch_events(
            content=request.content,
            source_id=request.source_id,
            metadata=request.metadata,
        )
    except EmptyManualBatchError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    created_events = await create_raw_memory_events(session, events)
    raw_event_ids = [event.id for event in created_events]
    refactor_start = await start_refactor_run_from_raw_events(
        raw_event_ids=raw_event_ids,
        session=session,
        workflow_starter=workflow_starter,
    )

    return CreateManualRawMemoryBatchResponse(
        source_id=created_events[0].source_id or "",
        raw_event_ids=raw_event_ids,
        run_id=refactor_start.run_id,
        workflow_id=refactor_start.workflow_id,
        temporal_run_id=refactor_start.temporal_run_id,
        status=refactor_start.status,
    )


@router.get("", response_model=list[RawMemoryEvent])
async def list_events(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    unprocessed_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_async_session),
) -> list[RawMemoryEvent]:
    return await list_raw_memory_events(
        session,
        limit=limit,
        offset=offset,
        unprocessed_only=unprocessed_only,
    )


@router.post("", response_model=RawMemoryEvent, status_code=status.HTTP_201_CREATED)
async def create_event(
    request: CreateRawMemoryEventRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RawMemoryEvent:
    event = RawMemoryEvent(
        **request.model_dump(exclude_none=True),
    )
    return await create_raw_memory_event(session, event)

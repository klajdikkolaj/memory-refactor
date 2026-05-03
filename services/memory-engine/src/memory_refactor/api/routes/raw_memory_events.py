from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from memory_refactor.core.models import RawMemoryEvent
from memory_refactor.db.repositories.raw_memory_events import (
    create_raw_memory_event,
    list_raw_memory_events,
)
from memory_refactor.db.session import get_async_session

router = APIRouter(prefix="/raw-memory-events", tags=["raw-memory-events"])


class CreateRawMemoryEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    source_type: str
    source_id: str | None = None
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


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

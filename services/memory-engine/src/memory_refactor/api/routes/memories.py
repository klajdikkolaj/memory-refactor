from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from memory_refactor.core.models import MemoryUnit
from memory_refactor.db.repositories.memory_units import create_memory_unit, list_memory_units
from memory_refactor.db.session import get_async_session

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("", response_model=list[MemoryUnit])
async def list_memories(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> list[MemoryUnit]:
    return await list_memory_units(session, limit=limit, offset=offset)


@router.post("", response_model=MemoryUnit, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory: MemoryUnit,
    session: AsyncSession = Depends(get_async_session),
) -> MemoryUnit:
    return await create_memory_unit(session, memory)

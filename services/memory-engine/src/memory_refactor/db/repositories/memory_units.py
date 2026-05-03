from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from memory_refactor.core.models import MemorySource, MemoryUnit
from memory_refactor.db.tables import MemorySourceRecord, MemoryUnitRecord


def memory_unit_from_record(record: MemoryUnitRecord) -> MemoryUnit:
    return MemoryUnit(
        id=record.id,
        kind=record.kind,
        content=record.content,
        confidence=record.confidence,
        status=record.status,
        sources=[
            MemorySource(
                source_type=source.source_type,
                source_id=source.source_id,
                raw_event_id=source.raw_event_id,
                excerpt=source.excerpt,
                url=source.url,
                captured_at=source.captured_at,
            )
            for source in record.sources
        ],
        metadata=record.extra,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def memory_unit_to_record(memory: MemoryUnit) -> MemoryUnitRecord:
    return MemoryUnitRecord(
        id=memory.id,
        kind=memory.kind.value,
        content=memory.content,
        confidence=memory.confidence,
        status=memory.status.value,
        extra=memory.metadata,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        sources=[
            MemorySourceRecord(
                source_type=source.source_type,
                source_id=source.source_id,
                raw_event_id=source.raw_event_id,
                excerpt=source.excerpt,
                url=source.url,
                captured_at=source.captured_at,
            )
            for source in memory.sources
        ],
    )


async def list_memory_units(
    session: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[MemoryUnit]:
    statement = (
        select(MemoryUnitRecord)
        .options(selectinload(MemoryUnitRecord.sources))
        .order_by(MemoryUnitRecord.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.scalars(statement)
    return [memory_unit_from_record(record) for record in result]


async def list_memory_units_by_ids(
    session: AsyncSession,
    memory_ids: list[str],
) -> list[MemoryUnit]:
    if not memory_ids:
        return []

    statement = (
        select(MemoryUnitRecord)
        .options(selectinload(MemoryUnitRecord.sources))
        .where(MemoryUnitRecord.id.in_(memory_ids))
    )
    result = await session.scalars(statement)
    records_by_id = {record.id: record for record in result}

    return [
        memory_unit_from_record(records_by_id[memory_id])
        for memory_id in memory_ids
        if memory_id in records_by_id
    ]


async def create_memory_unit(session: AsyncSession, memory: MemoryUnit) -> MemoryUnit:
    record = memory_unit_to_record(memory)
    session.add(record)
    await session.commit()

    statement = (
        select(MemoryUnitRecord)
        .options(selectinload(MemoryUnitRecord.sources))
        .where(MemoryUnitRecord.id == record.id)
    )
    result = await session.scalars(statement)
    created = result.one()
    return memory_unit_from_record(created)

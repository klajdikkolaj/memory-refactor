from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from memory_refactor.core.models import RawMemoryEvent
from memory_refactor.db.tables import RawMemoryEventRecord


def raw_memory_event_from_record(record: RawMemoryEventRecord) -> RawMemoryEvent:
    return RawMemoryEvent(
        id=record.id,
        source_type=record.source_type,
        source_id=record.source_id,
        content=record.content,
        metadata=record.extra,
        created_at=record.created_at,
        processed_at=record.processed_at,
    )


def raw_memory_event_to_record(event: RawMemoryEvent) -> RawMemoryEventRecord:
    return RawMemoryEventRecord(
        id=event.id,
        source_type=event.source_type,
        source_id=event.source_id,
        content=event.content,
        extra=event.metadata,
        created_at=event.created_at,
        processed_at=event.processed_at,
    )


async def list_raw_memory_events(
    session: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
    unprocessed_only: bool = False,
) -> list[RawMemoryEvent]:
    statement = select(RawMemoryEventRecord).order_by(RawMemoryEventRecord.created_at.desc())
    if unprocessed_only:
        statement = statement.where(RawMemoryEventRecord.processed_at.is_(None))

    statement = statement.limit(limit).offset(offset)
    result = await session.scalars(statement)
    return [raw_memory_event_from_record(record) for record in result]


async def list_raw_memory_events_by_ids(
    session: AsyncSession,
    event_ids: list[str],
) -> list[RawMemoryEvent]:
    if not event_ids:
        return []

    statement = select(RawMemoryEventRecord).where(RawMemoryEventRecord.id.in_(event_ids))
    result = await session.scalars(statement)
    records_by_id = {record.id: record for record in result}

    return [
        raw_memory_event_from_record(records_by_id[event_id])
        for event_id in event_ids
        if event_id in records_by_id
    ]


async def create_raw_memory_event(
    session: AsyncSession,
    event: RawMemoryEvent,
) -> RawMemoryEvent:
    record = raw_memory_event_to_record(event)
    session.add(record)
    await session.commit()

    return raw_memory_event_from_record(record)


async def create_raw_memory_events(
    session: AsyncSession,
    events: list[RawMemoryEvent],
) -> list[RawMemoryEvent]:
    records = [raw_memory_event_to_record(event) for event in events]

    async with session.begin():
        session.add_all(records)

    return [raw_memory_event_from_record(record) for record in records]


async def mark_raw_memory_events_processed(
    session: AsyncSession,
    event_ids: list[str],
    *,
    processed_at: datetime | None = None,
) -> list[RawMemoryEvent]:
    processed_at = processed_at or datetime.now(timezone.utc)
    await session.execute(
        update(RawMemoryEventRecord)
        .where(RawMemoryEventRecord.id.in_(event_ids))
        .values(processed_at=processed_at)
    )
    await session.commit()
    return await list_raw_memory_events_by_ids(session, event_ids)

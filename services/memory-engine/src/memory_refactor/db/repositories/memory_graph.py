from datetime import datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from memory_refactor.core.models import MemoryRelationship
from memory_refactor.db.tables import MemoryRelationshipRecord


def memory_relationship_from_record(record: MemoryRelationshipRecord) -> MemoryRelationship:
    return MemoryRelationship(
        id=record.id,
        subject=record.subject,
        predicate=record.predicate,
        object_id=record.object_id,
        source_memory_id=record.source_memory_id,
        confidence=record.confidence,
        valid_from=record.valid_from,
        valid_until=record.valid_until,
        metadata=record.extra,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def memory_relationship_to_record(relationship: MemoryRelationship) -> MemoryRelationshipRecord:
    return MemoryRelationshipRecord(
        id=relationship.id,
        subject=relationship.subject,
        predicate=relationship.predicate,
        object_id=relationship.object_id,
        source_memory_id=relationship.source_memory_id,
        confidence=relationship.confidence,
        valid_from=relationship.valid_from,
        valid_until=relationship.valid_until,
        extra=relationship.metadata,
        created_at=relationship.created_at,
        updated_at=relationship.updated_at,
    )


async def create_memory_relationship(
    session: AsyncSession,
    relationship: MemoryRelationship,
) -> MemoryRelationship:
    record = memory_relationship_to_record(relationship)
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return memory_relationship_from_record(record)


async def list_memory_relationships(
    session: AsyncSession,
    *,
    subject: str | None = None,
    predicate: str | None = None,
    object_id: str | None = None,
    source_memory_id: str | None = None,
    at: datetime | None = None,
    limit: int = 100,
) -> list[MemoryRelationship]:
    statement = select(MemoryRelationshipRecord).order_by(
        MemoryRelationshipRecord.updated_at.desc(),
        MemoryRelationshipRecord.id,
    )

    if subject is not None:
        statement = statement.where(MemoryRelationshipRecord.subject == subject)
    if predicate is not None:
        statement = statement.where(MemoryRelationshipRecord.predicate == predicate)
    if object_id is not None:
        statement = statement.where(MemoryRelationshipRecord.object_id == object_id)
    if source_memory_id is not None:
        statement = statement.where(MemoryRelationshipRecord.source_memory_id == source_memory_id)
    if at is not None:
        statement = statement.where(
            or_(
                MemoryRelationshipRecord.valid_from.is_(None),
                MemoryRelationshipRecord.valid_from <= at,
            )
        ).where(
            or_(
                MemoryRelationshipRecord.valid_until.is_(None),
                MemoryRelationshipRecord.valid_until > at,
            )
        )

    result = await session.scalars(statement.limit(limit))
    return [memory_relationship_from_record(record) for record in result]


class PostgresMemoryGraph:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def link_temporal_fact(
        self,
        subject: str,
        predicate: str,
        object_id: str,
        source_memory_id: str,
        *,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        confidence: float = 0.75,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRelationship:
        relationship = MemoryRelationship(
            subject=subject,
            predicate=predicate,
            object_id=object_id,
            source_memory_id=source_memory_id,
            confidence=confidence,
            valid_from=valid_from,
            valid_until=valid_until,
            metadata=metadata or {},
        )
        return await create_memory_relationship(self._session, relationship)

    async def list_temporal_facts(
        self,
        *,
        subject: str | None = None,
        predicate: str | None = None,
        at: datetime | None = None,
        limit: int = 100,
    ) -> list[MemoryRelationship]:
        return await list_memory_relationships(
            self._session,
            subject=subject,
            predicate=predicate,
            at=at,
            limit=limit,
        )

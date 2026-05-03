from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from memory_refactor.core.models import (
    EmbeddingVector,
    MemoryEmbedding,
    MemorySearchResult,
    MemoryStatus,
)
from memory_refactor.db.repositories.memory_units import memory_unit_from_record
from memory_refactor.db.tables import MemoryEmbeddingRecord, MemoryUnitRecord


def _vector_values(values: object) -> list[float]:
    if hasattr(values, "tolist"):
        values = values.tolist()
    if not isinstance(values, Iterable):
        raise TypeError("embedding vector value must be iterable")
    return [float(value) for value in values]


def memory_embedding_from_record(record: MemoryEmbeddingRecord) -> MemoryEmbedding:
    return MemoryEmbedding(
        id=record.id,
        memory_id=record.memory_id,
        embedding_model=record.embedding_model,
        vector=EmbeddingVector(values=_vector_values(record.embedding)),
        content_hash=record.content_hash,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def memory_embedding_to_record(embedding: MemoryEmbedding) -> MemoryEmbeddingRecord:
    return MemoryEmbeddingRecord(
        id=embedding.id,
        memory_id=embedding.memory_id,
        embedding_model=embedding.embedding_model,
        dimensions=embedding.vector.dimensions,
        embedding=embedding.vector.values,
        content_hash=embedding.content_hash,
        created_at=embedding.created_at,
        updated_at=embedding.updated_at,
    )


async def upsert_memory_embedding(
    session: AsyncSession,
    embedding: MemoryEmbedding,
) -> MemoryEmbedding:
    values = {
        "id": embedding.id,
        "memory_id": embedding.memory_id,
        "embedding_model": embedding.embedding_model,
        "dimensions": embedding.vector.dimensions,
        "embedding": embedding.vector.values,
        "content_hash": embedding.content_hash,
        "created_at": embedding.created_at,
        "updated_at": embedding.updated_at,
    }
    statement = insert(MemoryEmbeddingRecord).values(**values)
    statement = statement.on_conflict_do_update(
        constraint="uq_memory_embeddings_memory_model_dimensions",
        set_={
            "embedding": statement.excluded.embedding,
            "content_hash": statement.excluded.content_hash,
            "updated_at": statement.excluded.updated_at,
        },
    ).returning(MemoryEmbeddingRecord)

    result = await session.scalars(statement)
    record = result.one()
    await session.commit()
    return memory_embedding_from_record(record)


async def search_nearest_memories(
    session: AsyncSession,
    query: EmbeddingVector,
    *,
    limit: int = 20,
    embedding_model: str | None = None,
) -> list[MemorySearchResult]:
    distance = MemoryEmbeddingRecord.embedding.l2_distance(query.values)
    statement = (
        select(
            MemoryUnitRecord,
            MemoryEmbeddingRecord.embedding_model,
            distance.label("distance"),
        )
        .join(MemoryEmbeddingRecord, MemoryEmbeddingRecord.memory_id == MemoryUnitRecord.id)
        .options(selectinload(MemoryUnitRecord.sources))
        .where(MemoryEmbeddingRecord.dimensions == query.dimensions)
        .where(MemoryUnitRecord.status == MemoryStatus.ACTIVE.value)
        .order_by(distance)
        .limit(limit)
    )

    if embedding_model is not None:
        statement = statement.where(MemoryEmbeddingRecord.embedding_model == embedding_model)

    result = await session.execute(statement)
    return [
        MemorySearchResult(
            memory=memory_unit_from_record(memory_record),
            distance=float(distance_value),
            embedding_model=result_embedding_model,
        )
        for memory_record, result_embedding_model, distance_value in result.all()
    ]


class PostgresVectorIndex:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_memory_embedding(self, embedding: MemoryEmbedding) -> MemoryEmbedding:
        return await upsert_memory_embedding(self._session, embedding)

    async def search_nearest(
        self,
        query: EmbeddingVector,
        *,
        limit: int = 20,
        embedding_model: str | None = None,
    ) -> list[MemorySearchResult]:
        return await search_nearest_memories(
            self._session,
            query,
            limit=limit,
            embedding_model=embedding_model,
        )

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from memory_refactor.core.models import EmbeddingVector, MemoryEmbedding, MemoryKind, MemoryUnit
from memory_refactor.db import tables  # noqa: F401
from memory_refactor.db.base import Base
from memory_refactor.db.repositories.memory_units import create_memory_unit
from memory_refactor.db.repositories.vector_index import PostgresVectorIndex
from memory_refactor.db.session import create_engine

pytestmark = pytest.mark.integration


async def _reset_database(engine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_postgres_vector_index_returns_nearest_memory_candidates() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        await create_memory_unit(
            session,
            MemoryUnit(
                id="mem_python",
                kind=MemoryKind.SKILL,
                content="The user writes Python services.",
            ),
        )
        await create_memory_unit(
            session,
            MemoryUnit(
                id="mem_design",
                kind=MemoryKind.PREFERENCE,
                content="The user prefers calm product design.",
            ),
        )

        index = PostgresVectorIndex(session)
        await index.upsert_memory_embedding(
            MemoryEmbedding(
                id="emb_python",
                memory_id="mem_python",
                embedding_model="test-embedding",
                vector=EmbeddingVector(values=[1.0, 0.0, 0.0]),
            )
        )
        await index.upsert_memory_embedding(
            MemoryEmbedding(
                id="emb_design",
                memory_id="mem_design",
                embedding_model="test-embedding",
                vector=EmbeddingVector(values=[0.0, 1.0, 0.0]),
            )
        )

        results = await index.search_nearest(
            EmbeddingVector(values=[0.9, 0.1, 0.0]),
            embedding_model="test-embedding",
            limit=2,
        )

    await engine.dispose()

    assert [result.memory.id for result in results] == ["mem_python", "mem_design"]
    assert results[0].distance < results[1].distance
    assert {result.embedding_model for result in results} == {"test-embedding"}

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from memory_refactor.core.models import MemoryKind, MemoryUnit
from memory_refactor.db.base import Base
from memory_refactor.db.repositories.memory_units import create_memory_unit, list_memory_units
from memory_refactor.db.session import create_engine
from memory_refactor.db import tables  # noqa: F401

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_and_list_memory_units_against_database() -> None:
    engine = create_engine()

    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        created = await create_memory_unit(
            session,
            MemoryUnit(kind=MemoryKind.GOAL, content="Persist canonical memory."),
        )
        memories = await list_memory_units(session)

    await engine.dispose()

    assert created.id
    assert [memory.content for memory in memories] == ["Persist canonical memory."]

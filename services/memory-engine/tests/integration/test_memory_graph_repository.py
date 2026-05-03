from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from memory_refactor.core.models import MemoryKind, MemoryUnit
from memory_refactor.db import tables  # noqa: F401
from memory_refactor.db.base import Base
from memory_refactor.db.repositories.memory_graph import (
    PostgresMemoryGraph,
    list_memory_relationships,
)
from memory_refactor.db.repositories.memory_units import create_memory_unit
from memory_refactor.db.session import create_engine

pytestmark = pytest.mark.integration


async def _reset_database(engine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_postgres_memory_graph_lists_temporally_valid_relationships() -> None:
    engine = create_engine()
    await _reset_database(engine)

    may_1 = datetime(2026, 5, 1, tzinfo=timezone.utc)
    may_15 = datetime(2026, 5, 15, tzinfo=timezone.utc)
    june_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    july_1 = datetime(2026, 7, 1, tzinfo=timezone.utc)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        await create_memory_unit(
            session,
            MemoryUnit(
                id="mem_current_project",
                kind=MemoryKind.PROJECT,
                content="The user works on Memory Refactor.",
            ),
        )
        await create_memory_unit(
            session,
            MemoryUnit(
                id="mem_old_project",
                kind=MemoryKind.PROJECT,
                content="The user previously worked on a CRM dashboard.",
            ),
        )

        graph = PostgresMemoryGraph(session)
        current = await graph.link_temporal_fact(
            "user",
            "works_on",
            "memory-refactor",
            "mem_current_project",
            valid_from=may_1,
            confidence=0.9,
            metadata={"source": "manual"},
        )
        await graph.link_temporal_fact(
            "user",
            "works_on",
            "crm-dashboard",
            "mem_old_project",
            valid_from=may_1,
            valid_until=may_15,
            confidence=0.81,
        )

        active = await graph.list_temporal_facts(
            subject="user",
            predicate="works_on",
            at=june_1,
        )
        historical = await list_memory_relationships(
            session,
            subject="user",
            predicate="works_on",
            at=may_1,
        )
        future = await graph.list_temporal_facts(
            subject="user",
            predicate="works_on",
            at=july_1,
        )

    await engine.dispose()

    assert current.id.startswith("rel_")
    assert current.metadata == {"source": "manual"}
    assert [relationship.object_id for relationship in active] == ["memory-refactor"]
    assert {relationship.object_id for relationship in historical} == {
        "memory-refactor",
        "crm-dashboard",
    }
    assert [relationship.object_id for relationship in future] == ["memory-refactor"]

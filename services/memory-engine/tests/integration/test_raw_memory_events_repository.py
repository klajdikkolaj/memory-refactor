from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from memory_refactor.api.main import create_app
from memory_refactor.core.models import RawMemoryEvent
from memory_refactor.db import tables  # noqa: F401
from memory_refactor.db.base import Base
from memory_refactor.db.repositories.raw_memory_events import (
    create_raw_memory_event,
    list_raw_memory_events,
    list_raw_memory_events_by_ids,
    mark_raw_memory_events_processed,
)
from memory_refactor.db.session import create_engine, get_async_session

pytestmark = pytest.mark.integration


async def _reset_database(engine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_create_list_and_mark_raw_events_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        created = await create_raw_memory_event(
            session,
            RawMemoryEvent(
                id="evt_stack",
                source_type="manual",
                source_id="paste_1",
                content="I use Go, React, NestJS, and Vue.",
            ),
        )
        await create_raw_memory_event(
            session,
            RawMemoryEvent(
                id="evt_goal",
                source_type="manual",
                source_id="paste_1",
                content="I want to become an RL developer.",
            ),
        )
        events = await list_raw_memory_events(session)
        selected = await list_raw_memory_events_by_ids(session, ["evt_goal", "evt_stack"])
        processed = await mark_raw_memory_events_processed(session, ["evt_stack"])
        unprocessed = await list_raw_memory_events(session, unprocessed_only=True)

    await engine.dispose()

    assert created.id == "evt_stack"
    assert [event.id for event in selected] == ["evt_goal", "evt_stack"]
    assert {event.id for event in events} == {"evt_stack", "evt_goal"}
    assert processed[0].processed_at is not None
    assert [event.id for event in unprocessed] == ["evt_goal"]


@pytest.mark.asyncio
async def test_raw_memory_event_api_persists_events_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_async_session] = override_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            created_response = await client.post(
                "/raw-memory-events",
                json={
                    "id": "evt_api",
                    "source_type": "manual",
                    "source_id": "paste_api",
                    "content": "I prefer detailed mentor-style explanations.",
                },
            )
            list_response = await client.get("/raw-memory-events?unprocessed_only=true")
    finally:
        app.dependency_overrides.clear()

    await engine.dispose()

    assert created_response.status_code == 201
    assert created_response.json()["id"] == "evt_api"
    assert list_response.status_code == 200
    assert [event["id"] for event in list_response.json()] == ["evt_api"]

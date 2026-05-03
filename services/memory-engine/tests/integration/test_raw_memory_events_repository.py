from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from memory_refactor.api.main import create_app
from memory_refactor.api.routes.refactor_runs import get_refactor_workflow_starter
from memory_refactor.core.models import RawMemoryEvent, RefactorRunStatus
from memory_refactor.db import tables  # noqa: F401
from memory_refactor.db.base import Base
from memory_refactor.db.repositories.raw_memory_events import (
    create_raw_memory_event,
    list_raw_memory_events,
    list_raw_memory_events_by_ids,
    mark_raw_memory_events_processed,
)
from memory_refactor.db.repositories.refactor_runs import list_refactor_plans
from memory_refactor.db.session import create_engine, get_async_session
from memory_refactor.worker.starter import RefactorWorkflowStart

pytestmark = pytest.mark.integration


async def _reset_database(engine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
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


@pytest.mark.asyncio
async def test_manual_batch_endpoint_creates_events_and_starts_workflow_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)

    class FakeWorkflowStarter:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, list[str]]] = []

        async def start(
            self,
            *,
            run_id: str,
            workflow_id: str,
            raw_event_ids: list[str],
        ) -> RefactorWorkflowStart:
            self.calls.append((run_id, workflow_id, raw_event_ids))
            return RefactorWorkflowStart(
                run_id=run_id,
                workflow_id=workflow_id,
                temporal_run_id="temporal_run_batch",
            )

    fake_starter = FakeWorkflowStarter()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_refactor_workflow_starter] = lambda: fake_starter

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/raw-memory-events/manual-batches",
                json={
                    "source_id": "paste_batch",
                    "content": "I use Go and React.\n\nI want to learn RL.",
                    "metadata": {"demo": True},
                },
            )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    async with sessionmaker() as session:
        events = await list_raw_memory_events_by_ids(session, payload["raw_event_ids"])
        plans = await list_refactor_plans(session)

    await engine.dispose()

    assert response.status_code == 202
    assert payload["source_id"] == "paste_batch"
    assert payload["status"] == RefactorRunStatus.RUNNING.value
    assert payload["temporal_run_id"] == "temporal_run_batch"
    assert payload["trace_id"] is None
    assert fake_starter.calls[0][2] == payload["raw_event_ids"]
    assert [event.content for event in events] == [
        "I use Go and React.",
        "I want to learn RL.",
    ]
    assert [event.source_id for event in events] == ["paste_batch", "paste_batch"]
    assert events[0].metadata["demo"] is True
    assert events[0].metadata["manual_batch"] == {
        "source_id": "paste_batch",
        "line_index": 0,
        "line_count": 2,
    }
    assert plans[0].run_id == payload["run_id"]
    assert plans[0].input_event_ids == payload["raw_event_ids"]
    assert plans[0].status is RefactorRunStatus.RUNNING


@pytest.mark.asyncio
async def test_manual_batch_endpoint_keeps_events_when_workflow_start_fails() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)

    class FailingWorkflowStarter:
        async def start(
            self,
            *,
            run_id: str,
            workflow_id: str,
            raw_event_ids: list[str],
        ) -> RefactorWorkflowStart:
            raise RuntimeError("Temporal unavailable")

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_refactor_workflow_starter] = lambda: FailingWorkflowStarter()

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/raw-memory-events/manual-batches",
                json={"content": "I use Go.\nI want to learn RL."},
            )
    finally:
        app.dependency_overrides.clear()

    async with sessionmaker() as session:
        events = await list_raw_memory_events(session)
        plans = await list_refactor_plans(session)

    await engine.dispose()

    assert response.status_code == 503
    assert response.json()["detail"] == "Temporal workflow start failed"
    assert {event.content for event in events} == {"I use Go.", "I want to learn RL."}
    assert len(plans) == 1
    assert plans[0].status is RefactorRunStatus.FAILED
    assert set(plans[0].input_event_ids) == {event.id for event in events}


@pytest.mark.asyncio
async def test_manual_batch_endpoint_rejects_whitespace_only_content() -> None:
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
            response = await client.post(
                "/raw-memory-events/manual-batches",
                json={"content": "\n \n"},
            )
    finally:
        app.dependency_overrides.clear()

    await engine.dispose()

    assert response.status_code == 422

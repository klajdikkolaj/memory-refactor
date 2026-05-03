from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from memory_refactor.api.main import create_app
from memory_refactor.api.routes.refactor_runs import get_refactor_workflow_starter
from memory_refactor.core.models import (
    MemoryKind,
    MemoryOperation,
    MemorySource,
    MemoryUnit,
    OperationKind,
    OperationReviewStatus,
    RawMemoryEvent,
    RefactorPlan,
    RefactorRunStatus,
)
from memory_refactor.core.operations import propose_seed_refactor_plan
from memory_refactor.db import tables  # noqa: F401
from memory_refactor.db.base import Base
from memory_refactor.db.repositories.raw_memory_events import (
    create_raw_memory_event,
    list_raw_memory_events,
)
from memory_refactor.db.repositories.memory_units import create_memory_unit, list_memory_units
from memory_refactor.db.repositories.refactor_runs import (
    create_refactor_run_shell,
    create_refactor_plan,
    get_refactor_plan,
    list_refactor_plans,
)
from memory_refactor.db.session import create_engine, dispose_engine, get_async_session
from memory_refactor.db.tables import MemoryUnitRecord, MemoryVersionRecord, RefactorRunRecord
from memory_refactor.worker.activities import create_refactor_plan as create_refactor_plan_activity
from memory_refactor.worker.starter import RefactorWorkflowStart

pytestmark = pytest.mark.integration


async def _reset_database(engine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


def _reviewable_plan(
    *,
    run_id: str = "run_review",
    operation_id: str = "op_review",
    status: RefactorRunStatus = RefactorRunStatus.NEEDS_REVIEW,
) -> RefactorPlan:
    plan = propose_seed_refactor_plan(
        [
            MemoryUnit(id="mem_ts", kind=MemoryKind.PREFERENCE, content="Use TypeScript for UI."),
            MemoryUnit(id="mem_py", kind=MemoryKind.PREFERENCE, content="Use Python for AI."),
        ]
    )

    return plan.model_copy(
        update={
            "run_id": run_id,
            "status": status,
            "operations": [
                plan.operations[0].model_copy(update={"id": operation_id}),
            ],
        }
    )


def _approved_create_memory_plan(
    *,
    run_id: str = "run_apply",
    operation_id: str = "op_apply",
    memory_id: str = "mem_apply",
    source_event_id: str = "evt_apply",
    review_status: OperationReviewStatus = OperationReviewStatus.APPROVED,
    status: RefactorRunStatus = RefactorRunStatus.NEEDS_REVIEW,
) -> RefactorPlan:
    proposed_memory = MemoryUnit(
        id=memory_id,
        kind=MemoryKind.SUMMARY,
        content="The user wants memory changes applied transactionally.",
        confidence=0.84,
        sources=[
            MemorySource(
                source_type="manual",
                source_id=source_event_id,
                raw_event_id=source_event_id,
                excerpt="Apply memory changes transactionally.",
            )
        ],
    )
    operation = MemoryOperation(
        id=operation_id,
        operation=OperationKind.CREATE_MEMORY,
        source_event_ids=[source_event_id],
        proposed_memory=proposed_memory,
        rationale="The source event states a durable memory requirement.",
        confidence=0.84,
        review_status=review_status,
    )

    return RefactorPlan(
        id=f"plan_{run_id}",
        run_id=run_id,
        status=status,
        summary="Create one clean memory from source evidence.",
        input_event_ids=[source_event_id],
        operations=[operation],
    )


async def _patch_operation_review(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    run_id: str,
    operation_id: str,
    decision: str,
):
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
            return await client.patch(
                f"/refactor-runs/{run_id}/operations/{operation_id}/review",
                json={"decision": decision},
            )
    finally:
        app.dependency_overrides.clear()


async def _post_operation_apply(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    run_id: str,
    operation_id: str,
):
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
            return await client.post(
                f"/refactor-runs/{run_id}/operations/{operation_id}/apply"
            )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_get_and_list_refactor_plans_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = propose_seed_refactor_plan(
        [
            MemoryUnit(id="mem_ts", kind=MemoryKind.PREFERENCE, content="Use TypeScript for UI."),
            MemoryUnit(id="mem_py", kind=MemoryKind.PREFERENCE, content="Use Python for AI."),
        ]
    )

    async with sessionmaker() as session:
        created = await create_refactor_plan(session, plan)
        fetched = await get_refactor_plan(session, plan.run_id)
        plans = await list_refactor_plans(session)

    await engine.dispose()

    assert created.id == plan.id
    assert created.run_id == plan.run_id
    assert fetched is not None
    assert fetched.operations[0].source_memory_ids == ["mem_ts", "mem_py"]
    assert [stored_plan.run_id for stored_plan in plans] == [plan.run_id]


@pytest.mark.asyncio
async def test_preview_endpoint_persists_refactor_plan_against_database() -> None:
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
            response = await client.post("/refactor-runs/preview")
    finally:
        app.dependency_overrides.clear()

    async with sessionmaker() as session:
        plans = await list_refactor_plans(session)

    await engine.dispose()

    assert response.status_code == 201
    payload = response.json()
    assert payload["run_id"] == plans[0].run_id
    assert payload["operations"][0]["operation"] == "merge_memories"
    assert plans[0].summary == "Seed refactor plan with one merge operation."


@pytest.mark.asyncio
async def test_review_endpoint_approves_operation_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _reviewable_plan()
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _patch_operation_review(
        sessionmaker,
        run_id=plan.run_id,
        operation_id=plan.operations[0].id,
        decision="approved",
    )

    async with sessionmaker() as session:
        stored = await get_refactor_plan(session, plan.run_id)

    await engine.dispose()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "op_review"
    assert payload["review_status"] == "approved"
    assert stored is not None
    assert stored.operations[0].review_status is OperationReviewStatus.APPROVED


@pytest.mark.asyncio
async def test_review_endpoint_rejects_operation_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _reviewable_plan(run_id="run_reject", operation_id="op_reject")
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _patch_operation_review(
        sessionmaker,
        run_id=plan.run_id,
        operation_id=plan.operations[0].id,
        decision="rejected",
    )

    async with sessionmaker() as session:
        stored = await get_refactor_plan(session, plan.run_id)

    await engine.dispose()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "op_reject"
    assert payload["review_status"] == "rejected"
    assert stored is not None
    assert stored.operations[0].review_status is OperationReviewStatus.REJECTED


@pytest.mark.asyncio
async def test_review_endpoint_returns_404_for_unknown_operation() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _reviewable_plan()
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _patch_operation_review(
        sessionmaker,
        run_id=plan.run_id,
        operation_id="op_missing",
        decision="approved",
    )

    await engine.dispose()

    assert response.status_code == 404
    assert response.json()["detail"] == "Memory operation not found"


@pytest.mark.asyncio
async def test_review_endpoint_rejects_non_reviewable_run() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _reviewable_plan(status=RefactorRunStatus.APPLIED)
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _patch_operation_review(
        sessionmaker,
        run_id=plan.run_id,
        operation_id=plan.operations[0].id,
        decision="approved",
    )

    await engine.dispose()

    assert response.status_code == 409
    assert response.json()["detail"] == "Refactor run is not awaiting review"


@pytest.mark.asyncio
async def test_apply_endpoint_applies_approved_create_memory_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _approved_create_memory_plan()
    async with sessionmaker() as session:
        await create_raw_memory_event(
            session,
            RawMemoryEvent(
                id="evt_apply",
                source_type="manual",
                content="Apply memory changes transactionally.",
            ),
        )
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _post_operation_apply(
        sessionmaker,
        run_id=plan.run_id,
        operation_id=plan.operations[0].id,
    )

    async with sessionmaker() as session:
        memories = await list_memory_units(session)
        version_records = list(await session.scalars(select(MemoryVersionRecord)))
        stored = await get_refactor_plan(session, plan.run_id)

    await engine.dispose()

    assert response.status_code == 200
    payload = response.json()
    assert payload["operation"]["id"] == "op_apply"
    assert payload["operation"]["review_status"] == "applied"
    assert payload["memory"]["id"] == "mem_apply"
    assert [memory.id for memory in memories] == ["mem_apply"]
    assert memories[0].sources[0].raw_event_id == "evt_apply"
    assert len(version_records) == 1
    assert version_records[0].memory_id == "mem_apply"
    assert version_records[0].version == 1
    assert version_records[0].operation_id == "op_apply"
    assert version_records[0].snapshot["id"] == "mem_apply"
    assert stored is not None
    assert stored.status is RefactorRunStatus.APPLIED
    assert stored.operations[0].review_status is OperationReviewStatus.APPLIED


@pytest.mark.asyncio
async def test_apply_endpoint_rejects_non_approved_operation_without_writes() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _approved_create_memory_plan(
        run_id="run_not_approved",
        operation_id="op_not_approved",
        review_status=OperationReviewStatus.NEEDS_REVIEW,
    )
    async with sessionmaker() as session:
        await create_raw_memory_event(
            session,
            RawMemoryEvent(
                id="evt_apply",
                source_type="manual",
                content="Apply memory changes transactionally.",
            ),
        )
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _post_operation_apply(
        sessionmaker,
        run_id=plan.run_id,
        operation_id=plan.operations[0].id,
    )

    async with sessionmaker() as session:
        memory_ids = list(await session.scalars(select(MemoryUnitRecord.id)))
        version_ids = list(await session.scalars(select(MemoryVersionRecord.id)))
        stored = await get_refactor_plan(session, plan.run_id)

    await engine.dispose()

    assert response.status_code == 409
    assert response.json()["detail"] == "Memory operation is not approved"
    assert memory_ids == []
    assert version_ids == []
    assert stored is not None
    assert stored.operations[0].review_status is OperationReviewStatus.NEEDS_REVIEW


@pytest.mark.asyncio
async def test_apply_endpoint_rejects_missing_source_evidence_without_writes() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _approved_create_memory_plan(run_id="run_missing_source")
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _post_operation_apply(
        sessionmaker,
        run_id=plan.run_id,
        operation_id=plan.operations[0].id,
    )

    async with sessionmaker() as session:
        memory_ids = list(await session.scalars(select(MemoryUnitRecord.id)))
        version_ids = list(await session.scalars(select(MemoryVersionRecord.id)))
        stored = await get_refactor_plan(session, plan.run_id)

    await engine.dispose()

    assert response.status_code == 422
    assert response.json()["detail"] == "Source evidence not found: evt_apply"
    assert memory_ids == []
    assert version_ids == []
    assert stored is not None
    assert stored.operations[0].review_status is OperationReviewStatus.APPROVED


@pytest.mark.asyncio
async def test_apply_endpoint_rejects_duplicate_proposed_memory_without_marking_applied() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _approved_create_memory_plan(run_id="run_duplicate")
    async with sessionmaker() as session:
        await create_raw_memory_event(
            session,
            RawMemoryEvent(
                id="evt_apply",
                source_type="manual",
                content="Apply memory changes transactionally.",
            ),
        )
    async with sessionmaker() as session:
        await create_memory_unit(
            session,
            MemoryUnit(
                id="mem_apply",
                kind=MemoryKind.SUMMARY,
                content="Existing memory with the proposed ID.",
            ),
        )
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _post_operation_apply(
        sessionmaker,
        run_id=plan.run_id,
        operation_id=plan.operations[0].id,
    )

    async with sessionmaker() as session:
        version_ids = list(await session.scalars(select(MemoryVersionRecord.id)))
        stored = await get_refactor_plan(session, plan.run_id)

    await engine.dispose()

    assert response.status_code == 409
    assert response.json()["detail"] == "Proposed memory already exists: mem_apply"
    assert version_ids == []
    assert stored is not None
    assert stored.operations[0].review_status is OperationReviewStatus.APPROVED


@pytest.mark.asyncio
async def test_apply_endpoint_rejects_unsupported_operation_kind() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _reviewable_plan(
        run_id="run_unsupported",
        operation_id="op_unsupported",
    )
    plan = plan.model_copy(
        update={
            "operations": [
                plan.operations[0].model_copy(
                    update={"review_status": OperationReviewStatus.APPROVED}
                )
            ]
        }
    )
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _post_operation_apply(
        sessionmaker,
        run_id=plan.run_id,
        operation_id=plan.operations[0].id,
    )

    async with sessionmaker() as session:
        memory_ids = list(await session.scalars(select(MemoryUnitRecord.id)))
        version_ids = list(await session.scalars(select(MemoryVersionRecord.id)))
        stored = await get_refactor_plan(session, plan.run_id)

    await engine.dispose()

    assert response.status_code == 422
    assert response.json()["detail"] == "Only approved create_memory operations can be applied in the MVP"
    assert memory_ids == []
    assert version_ids == []
    assert stored is not None
    assert stored.operations[0].review_status is OperationReviewStatus.APPROVED


@pytest.mark.asyncio
async def test_apply_endpoint_returns_404_for_unknown_operation() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    plan = _approved_create_memory_plan()
    async with sessionmaker() as session:
        await create_refactor_plan(session, plan)

    response = await _post_operation_apply(
        sessionmaker,
        run_id=plan.run_id,
        operation_id="op_missing",
    )

    await engine.dispose()

    assert response.status_code == 404
    assert response.json()["detail"] == "Memory operation not found"


@pytest.mark.asyncio
async def test_start_endpoint_records_running_temporal_workflow_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    for event in [
        RawMemoryEvent(id="evt_stack", source_type="manual", content="I use Go and React."),
        RawMemoryEvent(id="evt_goal", source_type="manual", content="I want to learn RL."),
    ]:
        async with sessionmaker() as session:
            await create_raw_memory_event(session, event)

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
                temporal_run_id="temporal_run_test",
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
                "/refactor-runs",
                json={"raw_event_ids": ["evt_stack", "evt_goal"]},
            )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    async with sessionmaker() as session:
        record = await session.get(RefactorRunRecord, payload["run_id"])
        plans = await list_refactor_plans(session)

    await engine.dispose()

    assert response.status_code == 202
    assert payload["workflow_id"] == f"refactor-{payload['run_id']}"
    assert payload["temporal_run_id"] == "temporal_run_test"
    assert payload["status"] == RefactorRunStatus.RUNNING.value
    assert fake_starter.calls[0][0] == payload["run_id"]
    assert fake_starter.calls[0][2] == ["evt_stack", "evt_goal"]
    assert record is not None
    assert record.workflow_id == payload["workflow_id"]
    assert record.input_event_ids == ["evt_stack", "evt_goal"]
    assert plans[0].status is RefactorRunStatus.RUNNING
    assert plans[0].operations == []


@pytest.mark.asyncio
async def test_start_endpoint_marks_run_failed_when_temporal_start_fails() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        await create_raw_memory_event(
            session,
            RawMemoryEvent(id="evt_stack", source_type="manual", content="I use Go."),
        )

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
            response = await client.post("/refactor-runs", json={"raw_event_ids": ["evt_stack"]})
    finally:
        app.dependency_overrides.clear()

    async with sessionmaker() as session:
        plans = await list_refactor_plans(session)

    await engine.dispose()

    assert response.status_code == 503
    assert response.json()["detail"] == "Temporal workflow start failed"
    assert len(plans) == 1
    assert plans[0].status is RefactorRunStatus.FAILED


@pytest.mark.asyncio
async def test_refactor_workflow_activity_persists_completed_plan_against_database() -> None:
    engine = create_engine()
    await _reset_database(engine)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)

    for event in [
        RawMemoryEvent(
            id="evt_stack",
            source_type="manual",
            content="I use Go, React, NestJS, and Vue.",
        ),
        RawMemoryEvent(
            id="evt_goal",
            source_type="manual",
            content="I am learning ML because I want to become an RL developer.",
        ),
    ]:
        async with sessionmaker() as session:
            await create_raw_memory_event(session, event)

    async with sessionmaker() as session:
        await create_refactor_run_shell(
            session,
            run_id="run_activity",
            workflow_id="refactor-run_activity",
            summary="Temporal refactor workflow is queued.",
            input_event_ids=["evt_stack", "evt_goal"],
        )

    payload = await create_refactor_plan_activity(
        {
            "run_id": "run_activity",
            "raw_event_ids": ["evt_stack", "evt_goal"],
        }
    )

    async with sessionmaker() as session:
        plan = await get_refactor_plan(session, "run_activity")
        events = await list_raw_memory_events(session)

    await dispose_engine()
    await engine.dispose()

    assert payload["run_id"] == "run_activity"
    assert payload["status"] == RefactorRunStatus.NEEDS_REVIEW.value
    assert payload["operations"][0]["source_event_ids"] == ["evt_stack", "evt_goal"]
    assert plan is not None
    assert plan.status is RefactorRunStatus.NEEDS_REVIEW
    assert plan.operations[0].operation == "create_memory"
    assert plan.operations[0].source_event_ids == ["evt_stack", "evt_goal"]
    assert all(event.processed_at is not None for event in events)

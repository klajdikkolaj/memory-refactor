from temporalio import activity

from memory_refactor.core.models import RefactorPlan, RefactorRunStatus, RefactorWorkflowInput
from memory_refactor.core.operations import propose_seed_refactor_plan_from_raw_events
from memory_refactor.db.repositories.raw_memory_events import list_raw_memory_events_by_ids
from memory_refactor.db.repositories.refactor_runs import (
    complete_refactor_plan_and_mark_events_processed,
    update_refactor_run_status,
)
from memory_refactor.db.session import get_sessionmaker


@activity.defn
async def create_refactor_plan(workflow_payload: dict) -> dict:
    workflow_input = RefactorWorkflowInput.model_validate(workflow_payload)
    sessionmaker = get_sessionmaker()

    try:
        async with sessionmaker() as session:
            events = await list_raw_memory_events_by_ids(session, workflow_input.raw_event_ids)

        found_event_ids = {event.id for event in events}
        missing_event_ids = [
            event_id for event_id in workflow_input.raw_event_ids if event_id not in found_event_ids
        ]
        if missing_event_ids:
            raise ValueError(f"Unknown raw event ids: {', '.join(missing_event_ids)}")

        plan: RefactorPlan = propose_seed_refactor_plan_from_raw_events(events)
        plan = plan.model_copy(
            update={
                "run_id": workflow_input.run_id,
                "status": RefactorRunStatus.NEEDS_REVIEW,
                "input_event_ids": workflow_input.raw_event_ids,
            }
        )

        async with sessionmaker() as session:
            completed = await complete_refactor_plan_and_mark_events_processed(
                session,
                plan,
                workflow_input.raw_event_ids,
            )

        return completed.model_dump(mode="json")
    except Exception:
        async with sessionmaker() as session:
            await update_refactor_run_status(
                session,
                workflow_input.run_id,
                RefactorRunStatus.FAILED,
            )
        raise

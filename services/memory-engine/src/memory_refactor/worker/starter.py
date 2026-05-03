from typing import Protocol

from pydantic import BaseModel, ConfigDict
from temporalio.client import Client

from memory_refactor.core.models import RefactorWorkflowInput
from memory_refactor.core.settings import Settings, get_settings
from memory_refactor.worker.workflows import RefactorMemoryWorkflow


class RefactorWorkflowStart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow_id: str
    temporal_run_id: str | None = None


class RefactorWorkflowStarter(Protocol):
    async def start(
        self,
        *,
        run_id: str,
        workflow_id: str,
        raw_event_ids: list[str],
    ) -> RefactorWorkflowStart:
        ...


def build_refactor_workflow_id(run_id: str) -> str:
    return f"refactor-{run_id}"


class TemporalRefactorWorkflowStarter:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def start(
        self,
        *,
        run_id: str,
        workflow_id: str,
        raw_event_ids: list[str],
    ) -> RefactorWorkflowStart:
        client = await Client.connect(
            self._settings.temporal_address,
            namespace=self._settings.temporal_namespace,
        )
        workflow_input = RefactorWorkflowInput(run_id=run_id, raw_event_ids=raw_event_ids)
        handle = await client.start_workflow(
            RefactorMemoryWorkflow.run,
            workflow_input.model_dump(mode="json"),
            id=workflow_id,
            task_queue=self._settings.temporal_task_queue,
        )

        return RefactorWorkflowStart(
            run_id=run_id,
            workflow_id=handle.id,
            temporal_run_id=handle.first_execution_run_id,
        )


def get_refactor_workflow_starter() -> RefactorWorkflowStarter:
    return TemporalRefactorWorkflowStarter()

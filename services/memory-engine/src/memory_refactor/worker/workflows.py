from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from memory_refactor.worker.activities import create_refactor_plan


@workflow.defn
class RefactorMemoryWorkflow:
    @workflow.run
    async def run(self, workflow_payload: dict) -> dict:
        return await workflow.execute_activity(
            create_refactor_plan,
            workflow_payload,
            start_to_close_timeout=timedelta(minutes=5),
        )

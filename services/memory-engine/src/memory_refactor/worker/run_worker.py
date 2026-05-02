import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from memory_refactor.core.settings import get_settings
from memory_refactor.worker.activities import create_refactor_plan
from memory_refactor.worker.workflows import RefactorMemoryWorkflow


async def main() -> None:
    settings = get_settings()
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[RefactorMemoryWorkflow],
        activities=[create_refactor_plan],
    )
    await worker.run()


def cli() -> None:
    asyncio.run(main())

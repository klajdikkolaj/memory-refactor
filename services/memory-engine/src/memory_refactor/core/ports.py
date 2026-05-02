from typing import Protocol

from memory_refactor.core.models import MemoryOperation, MemoryUnit, RefactorPlan


class MemoryRepository(Protocol):
    async def list_related(self, query: str, limit: int = 20) -> list[MemoryUnit]:
        ...

    async def save_plan(self, plan: RefactorPlan) -> None:
        ...

    async def apply_operations(self, operations: list[MemoryOperation]) -> None:
        ...


class VectorIndex(Protocol):
    async def upsert_memory(self, memory: MemoryUnit) -> None:
        ...

    async def search(self, query: str, limit: int = 20) -> list[MemoryUnit]:
        ...


class MemoryGraph(Protocol):
    async def link_temporal_fact(
        self,
        subject: str,
        predicate: str,
        object_id: str,
        source_memory_id: str,
    ) -> None:
        ...


class RefactorAgent(Protocol):
    async def propose_plan(self, memories: list[MemoryUnit]) -> RefactorPlan:
        ...

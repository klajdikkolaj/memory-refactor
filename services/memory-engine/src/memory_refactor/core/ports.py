from datetime import datetime
from typing import Any, Protocol

from memory_refactor.core.models import (
    EmbeddingVector,
    MemoryEmbedding,
    MemoryOperation,
    MemoryRelationship,
    MemorySearchResult,
    MemoryUnit,
    RefactorPlan,
)


class MemoryRepository(Protocol):
    async def list_related(self, query: str, limit: int = 20) -> list[MemoryUnit]:
        ...

    async def save_plan(self, plan: RefactorPlan) -> None:
        ...

    async def apply_operations(self, operations: list[MemoryOperation]) -> None:
        ...


class VectorIndex(Protocol):
    async def upsert_memory_embedding(self, embedding: MemoryEmbedding) -> MemoryEmbedding:
        ...

    async def search_nearest(
        self,
        query: EmbeddingVector,
        *,
        limit: int = 20,
        embedding_model: str | None = None,
    ) -> list[MemorySearchResult]:
        ...


class MemoryGraph(Protocol):
    async def link_temporal_fact(
        self,
        subject: str,
        predicate: str,
        object_id: str,
        source_memory_id: str,
        *,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        confidence: float = 0.75,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRelationship:
        ...

    async def list_temporal_facts(
        self,
        *,
        subject: str | None = None,
        predicate: str | None = None,
        at: datetime | None = None,
        limit: int = 100,
    ) -> list[MemoryRelationship]:
        ...


class RefactorAgent(Protocol):
    async def propose_plan(self, memories: list[MemoryUnit]) -> RefactorPlan:
        ...

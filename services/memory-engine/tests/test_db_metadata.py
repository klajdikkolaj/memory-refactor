from memory_refactor.db.base import Base
from memory_refactor.db import tables  # noqa: F401


def test_database_metadata_contains_initial_tables() -> None:
    assert {
        "memory_units",
        "raw_memory_events",
        "memory_sources",
        "memory_embeddings",
        "memory_relationships",
        "refactor_runs",
        "memory_operations",
        "review_decisions",
        "memory_versions",
        "contradictions",
    }.issubset(Base.metadata.tables)

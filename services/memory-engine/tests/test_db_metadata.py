from memory_refactor.db.base import Base
from memory_refactor.db import tables  # noqa: F401


def test_database_metadata_contains_initial_tables() -> None:
    assert {
        "memory_units",
        "raw_memory_events",
        "memory_sources",
        "refactor_runs",
        "memory_operations",
        "memory_versions",
        "contradictions",
    }.issubset(Base.metadata.tables)

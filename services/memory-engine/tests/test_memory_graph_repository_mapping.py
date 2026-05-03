from datetime import datetime, timezone

from memory_refactor.core.models import MemoryRelationship
from memory_refactor.db.repositories.memory_graph import (
    memory_relationship_from_record,
    memory_relationship_to_record,
)


def test_memory_relationship_record_mapping_round_trips_contract_fields() -> None:
    valid_from = datetime(2026, 5, 1, tzinfo=timezone.utc)
    valid_until = datetime(2026, 6, 1, tzinfo=timezone.utc)
    captured_at = datetime(2026, 5, 3, tzinfo=timezone.utc)
    relationship = MemoryRelationship(
        id="rel_test",
        subject="user",
        predicate="works_on",
        object_id="memory-refactor",
        source_memory_id="mem_project",
        confidence=0.88,
        valid_from=valid_from,
        valid_until=valid_until,
        metadata={"scope": "project"},
        created_at=captured_at,
        updated_at=captured_at,
    )

    record = memory_relationship_to_record(relationship)
    mapped = memory_relationship_from_record(record)

    assert record.source_memory_id == "mem_project"
    assert record.extra == {"scope": "project"}
    assert mapped == relationship

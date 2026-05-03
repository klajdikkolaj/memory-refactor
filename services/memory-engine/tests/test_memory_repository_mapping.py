from datetime import datetime, timezone

from memory_refactor.core.models import MemoryKind, MemorySource, MemoryStatus, MemoryUnit
from memory_refactor.db.repositories.memory_units import memory_unit_from_record, memory_unit_to_record


def test_memory_unit_record_mapping_round_trips_contract_fields() -> None:
    captured_at = datetime(2026, 5, 2, tzinfo=timezone.utc)
    memory = MemoryUnit(
        id="mem_test",
        kind=MemoryKind.GOAL,
        content="Build a durable memory compiler.",
        confidence=0.91,
        status=MemoryStatus.ACTIVE,
        sources=[
            MemorySource(
                source_type="note",
                source_id="source_1",
                raw_event_id="evt_source_1",
                excerpt="Temporal plus typed operations.",
                captured_at=captured_at,
            )
        ],
        metadata={"topic": "architecture"},
        created_at=captured_at,
        updated_at=captured_at,
    )

    record = memory_unit_to_record(memory)
    mapped = memory_unit_from_record(record)

    assert mapped.id == "mem_test"
    assert mapped.kind is MemoryKind.GOAL
    assert mapped.content == "Build a durable memory compiler."
    assert mapped.confidence == 0.91
    assert mapped.sources[0].source_id == "source_1"
    assert mapped.sources[0].raw_event_id == "evt_source_1"
    assert mapped.metadata == {"topic": "architecture"}

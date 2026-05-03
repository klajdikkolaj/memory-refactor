from datetime import datetime, timezone

from memory_refactor.core.models import MemoryKind, MemorySource, MemoryStatus, MemoryUnit, MemoryVersion
from memory_refactor.db.repositories.memory_units import (
    memory_unit_from_record,
    memory_unit_to_record,
    memory_version_from_record,
    memory_version_to_record,
)


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


def test_memory_version_record_mapping_round_trips_contract_fields() -> None:
    captured_at = datetime(2026, 5, 3, tzinfo=timezone.utc)
    snapshot = MemoryUnit(
        id="mem_versioned",
        kind=MemoryKind.SUMMARY,
        content="The user wants clean memory with source evidence.",
        confidence=0.87,
        sources=[
            MemorySource(
                source_type="manual",
                source_id="batch_1",
                raw_event_id="evt_1",
                excerpt="Memory should cite sources.",
                captured_at=captured_at,
            )
        ],
        created_at=captured_at,
        updated_at=captured_at,
    )
    version = MemoryVersion(
        id="ver_1",
        memory_id="mem_versioned",
        version=1,
        snapshot=snapshot,
        operation_id="op_create",
        created_at=captured_at,
    )

    record = memory_version_to_record(version)
    mapped = memory_version_from_record(record)

    assert record.memory_id == "mem_versioned"
    assert record.version == 1
    assert record.operation_id == "op_create"
    assert mapped == version

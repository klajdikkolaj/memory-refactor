from datetime import datetime, timezone

from memory_refactor.core.models import RawMemoryEvent
from memory_refactor.db.repositories.raw_memory_events import (
    raw_memory_event_from_record,
    raw_memory_event_to_record,
)


def test_raw_memory_event_record_mapping_round_trips_contract_fields() -> None:
    created_at = datetime(2026, 5, 3, tzinfo=timezone.utc)
    event = RawMemoryEvent(
        id="evt_test",
        source_type="manual",
        source_id="paste_1",
        content="I use Go, React, NestJS, and Vue.",
        metadata={"batch": "demo"},
        created_at=created_at,
    )

    record = raw_memory_event_to_record(event)
    mapped = raw_memory_event_from_record(record)

    assert mapped.id == "evt_test"
    assert mapped.source_type == "manual"
    assert mapped.source_id == "paste_1"
    assert mapped.content == "I use Go, React, NestJS, and Vue."
    assert mapped.metadata == {"batch": "demo"}
    assert mapped.created_at == created_at
    assert mapped.processed_at is None

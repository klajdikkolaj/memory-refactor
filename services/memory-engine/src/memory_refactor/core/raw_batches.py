from typing import Any

from memory_refactor.core.ids import new_id
from memory_refactor.core.models import RawMemoryEvent


class EmptyManualBatchError(ValueError):
    pass


def split_manual_batch_content(content: str) -> list[str]:
    return [line.strip() for line in content.splitlines() if line.strip()]


def build_manual_batch_events(
    *,
    content: str,
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[RawMemoryEvent]:
    lines = split_manual_batch_content(content)
    if not lines:
        raise EmptyManualBatchError("Manual batch content must include at least one non-empty line.")

    batch_source_id = source_id or new_id("batch")
    base_metadata = metadata or {}
    event_count = len(lines)

    return [
        RawMemoryEvent(
            source_type="manual",
            source_id=batch_source_id,
            content=line,
            metadata={
                **base_metadata,
                "manual_batch": {
                    "source_id": batch_source_id,
                    "line_index": index,
                    "line_count": event_count,
                },
            },
        )
        for index, line in enumerate(lines)
    ]

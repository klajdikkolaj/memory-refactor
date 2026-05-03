import pytest

from memory_refactor.core.raw_batches import (
    EmptyManualBatchError,
    build_manual_batch_events,
    split_manual_batch_content,
)


def test_split_manual_batch_content_uses_non_empty_trimmed_lines() -> None:
    lines = split_manual_batch_content(
        """
        I use Go and React.

          I want to learn reinforcement learning.
        """
    )

    assert lines == [
        "I use Go and React.",
        "I want to learn reinforcement learning.",
    ]


def test_build_manual_batch_events_preserves_batch_metadata() -> None:
    events = build_manual_batch_events(
        content="I use Go.\nI prefer detailed examples.",
        source_id="paste_demo",
        metadata={"demo": True},
    )

    assert [event.content for event in events] == [
        "I use Go.",
        "I prefer detailed examples.",
    ]
    assert {event.source_type for event in events} == {"manual"}
    assert {event.source_id for event in events} == {"paste_demo"}
    assert events[0].metadata == {
        "demo": True,
        "manual_batch": {
            "source_id": "paste_demo",
            "line_index": 0,
            "line_count": 2,
        },
    }
    assert events[1].metadata["manual_batch"]["line_index"] == 1


def test_build_manual_batch_events_rejects_empty_batch() -> None:
    with pytest.raises(EmptyManualBatchError):
        build_manual_batch_events(content="\n \n", source_id="paste_empty")

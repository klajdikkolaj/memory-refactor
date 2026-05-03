import pytest
from pydantic import ValidationError

from memory_refactor.core.models import RefactorWorkflowInput
from memory_refactor.worker.starter import build_refactor_workflow_id


def test_refactor_workflow_input_uses_raw_event_ids() -> None:
    workflow_input = RefactorWorkflowInput(
        run_id="run_temporal",
        raw_event_ids=["evt_stack", "evt_goal"],
    )

    assert workflow_input.run_id == "run_temporal"
    assert workflow_input.raw_event_ids == ["evt_stack", "evt_goal"]


def test_refactor_workflow_input_requires_raw_event_ids() -> None:
    with pytest.raises(ValidationError):
        RefactorWorkflowInput(run_id="run_empty", raw_event_ids=[])


def test_refactor_workflow_id_is_derived_from_run_id() -> None:
    assert build_refactor_workflow_id("run_abc") == "refactor-run_abc"

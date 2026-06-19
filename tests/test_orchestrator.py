from __future__ import annotations

import json

from cad_agent.orchestrator import EXPORTED, SPEC_PENDING_APPROVAL, Workflow, audit_event


def test_state_machine_records_spec_approval_transition() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")

    assert workflow.state == "spec_approved"
    assert workflow.events[-1]["type"] == "specification_approved"
    assert workflow.approval_decisions[-1]["approved"] is True


def test_audit_event_shape_is_json_serializable() -> None:
    event = audit_event("specification_approved", traceability_id="tr_spec_1")

    assert event == {
        "type": "specification_approved",
        "traceability_id": "tr_spec_1",
        "payload": {"traceability_id": "tr_spec_1"},
    }
    assert json.dumps(event, sort_keys=True)


def test_validation_failure_creates_revision_request_with_reason_codes() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.start_validation("tr_val_1")

    result = workflow.handle_validation(
        {
            "passed": False,
            "reason_codes": ["WALL_THICKNESS_BELOW_MIN"],
            "failure_locations": ["manufacturing_profile_rules"],
        }
    )

    assert workflow.state == "revision_requested"
    assert result.blocked is True
    assert result.reason == "VALIDATION_FAILED"
    assert result.revision_request is not None
    assert result.revision_request.reason_codes == ["WALL_THICKNESS_BELOW_MIN"]
    assert result.revision_request.failure_locations == ["manufacturing_profile_rules"]
    assert [event["type"] for event in workflow.events[-2:]] == ["validation_failed", "revision_requested"]


def test_three_validation_failures_escalate_to_human() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.start_validation("tr_val_1")

    for _ in range(3):
        result = workflow.handle_validation({"passed": False, "reason_codes": ["RETRY_FAILURE"]})

    assert workflow.state == "escalated_to_human"
    assert result is not None
    assert result.blocked is True
    assert result.reason == "MAX_REVISION_LOOPS_REACHED"
    assert workflow.events[-1]["type"] == "validation_escalated_to_human"


def test_export_approval_moves_workflow_to_exported() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.mark_validation_passed("tr_val_1")

    request = workflow.request_export("tr_val_1")
    result = workflow.approve_export("export-1")

    assert request.blocked is True
    assert request.reason == "EXPORT_APPROVAL_REQUIRED"
    assert workflow.state == "exported"
    assert result.approved is True
    assert workflow.events[-1]["type"] == "export_approved"
    assert workflow.approval_decisions[-1]["approval_type"] == "export"


def test_invalid_state_transition_is_rejected() -> None:
    workflow = Workflow()

    workflow._transition(SPEC_PENDING_APPROVAL)

    try:
        workflow._transition(EXPORTED)
    except ValueError as exc:
        assert "invalid workflow transition" in str(exc)
    else:
        raise AssertionError("invalid transition was accepted")

from __future__ import annotations

import json

import pytest

import cad_agent.orchestrator as orchestrator
from cad_agent.assembly_checks import (
    AABB_INTERFERENCE,
    AssemblyPart,
    BBox,
    assembly_report_to_validation_result,
    check_interference,
)
from cad_agent.motion_validation import (
    INSUFFICIENT_CLEARANCE,
    validate_motion,
)
from cad_agent.orchestrator import (
    CAD_BUILT,
    CREATED,
    DSL_GENERATED,
    ESCALATED_TO_HUMAN,
    EXPORTED,
    SPEC_APPROVED,
    SPEC_PENDING_APPROVAL,
    VALIDATION_PASSED,
    MOTION_VALIDATION_PASSED_NOT_EXPORT_APPROVAL,
    NEW_OPERATION_APPROVAL_REQUIRED,
    Workflow,
    audit_event,
)


def passing_motion_validation_report() -> dict[str, object]:
    state = {
        "traceability_id": "tr_motion_gate_pass",
        "mechanism_id": "mech_gate_pass",
        "motion_type": "rotation",
        "rotation_axis": "z",
        "angular_range_deg": {"start_deg": 0.0, "end_deg": 90.0},
        "moving_part_ids": ["rotor"],
        "parts": [{"part_id": "rotor", "traceability_id": "tr_part_rotor_gate_pass"}],
    }
    return validate_motion(state).report


def failing_motion_validation_report() -> dict[str, object]:
    state = {"rotation_axis": "z", "clearance_mm": 0.2, "min_clearance_mm": 1.0}
    return validate_motion(state).report


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


def test_new_operation_requires_approval() -> None:
    result = orchestrator.request_new_operation("custom_gear")

    assert result.requires_human_approval is True
    assert result.reason_code == NEW_OPERATION_APPROVAL_REQUIRED


def test_workflow_new_operation_approval_request_blocks_and_records_audit(tmp_path) -> None:
    workflow = orchestrator.Workflow(audit_path=tmp_path / "audit.jsonl")

    result = workflow.request_new_operation_approval("custom_gear", traceability_id="tr_dsl_new_op")

    assert result.blocked is True
    assert result.reason == NEW_OPERATION_APPROVAL_REQUIRED
    assert workflow.state == ESCALATED_TO_HUMAN
    assert workflow.events[-1]["type"] == "new_operation_approval_required"
    assert workflow.events[-1]["payload"]["request"]["operation"] == "custom_gear"
    assert workflow.events[-1]["payload"]["request"]["requires_human_approval"] is True

    lines = (tmp_path / "audit.jsonl").read_text().splitlines()
    records = [json.loads(line) for line in lines]
    assert records[-1]["event_type"] == "new_operation_approval_required"
    assert records[-1]["payload"]["request"]["reason_code"] == NEW_OPERATION_APPROVAL_REQUIRED


def test_validation_failure_creates_revision_request() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")

    result = workflow.handle_validation({"passed": False, "reason_codes": ["WALL_THICKNESS_BELOW_MIN"]})

    assert workflow.state == "revision_requested"
    assert workflow.failure_count == 1
    assert result.revision_request is not None
    assert result.revision_request.reason_codes == ["WALL_THICKNESS_BELOW_MIN"]


def test_assembly_failure_blocks_export_through_workflow_gate() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.run_cad({"traceability_id": "tr_assembly"})
    workflow.start_validation("tr_assembly")
    assembly_report = check_interference(
        [
            AssemblyPart("a", "tr_a", BBox(0, 0, 0, 10, 10, 10)),
            AssemblyPart("b", "tr_b", BBox(5, 5, 5, 15, 15, 15)),
        ]
    )

    result = workflow.handle_assembly_validation(assembly_report_to_validation_result(assembly_report), traceability_id="tr_assembly")
    export_result = workflow.request_export("tr_assembly")

    assert workflow.state == "revision_requested"
    assert result.blocked is True
    assert result.revision_request is not None
    assert result.revision_request.reason_codes == [AABB_INTERFERENCE]
    assert export_result.blocked is True
    assert export_result.reason == "VALIDATION_NOT_PASSED"


def test_motion_failure_blocks_export_through_workflow_gate() -> None:
    workflow = Workflow()
    motion_result = workflow.handle_motion_validation(failing_motion_validation_report())

    export_result = workflow.request_export("tr_motion")

    assert workflow.state == "revision_requested"
    assert motion_result.blocked is True
    assert motion_result.revision_request is not None
    assert motion_result.revision_request.reason_codes[0] == INSUFFICIENT_CLEARANCE
    assert INSUFFICIENT_CLEARANCE in motion_result.revision_request.reason_codes
    assert export_result.blocked is True
    assert export_result.reason == "VALIDATION_NOT_PASSED"


def test_motion_validation_pass_does_not_approve_export_from_created() -> None:
    workflow = Workflow()

    result = workflow.handle_motion_validation(passing_motion_validation_report())
    export_result = workflow.request_export("tr_motion_pass")

    assert workflow.state == CREATED
    assert result.blocked is True
    assert result.reason == MOTION_VALIDATION_PASSED_NOT_EXPORT_APPROVAL
    assert export_result.blocked is True
    assert export_result.reason == "VALIDATION_NOT_PASSED"


def test_motion_validation_pass_does_not_replace_export_approval() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.run_cad({"traceability_id": "tr_motion_pass"})
    workflow.start_validation("tr_motion_pass")

    result = workflow.handle_motion_validation(passing_motion_validation_report())

    assert workflow.state == VALIDATION_PASSED
    assert result.approved is True

    export_result = workflow.request_export("tr_motion_pass")

    assert export_result.blocked is True
    assert export_result.reason == "EXPORT_APPROVAL_REQUIRED"


def test_validation_failure_from_created_is_rejected() -> None:
    workflow = Workflow()

    with pytest.raises(ValueError, match="invalid workflow transition"):
        workflow.handle_validation({"passed": False, "reason_codes": ["RETRY_FAILURE"]})

    assert workflow.state == CREATED
    assert workflow.failure_count == 0
    assert workflow.revision_requests == []


def test_three_failures_escalate_to_human() -> None:
    workflow = Workflow()

    for index in range(3):
        if index > 0:
            workflow._transition(SPEC_PENDING_APPROVAL)
            workflow.approve_specification(f"spec_retry_{index}")
        else:
            workflow.approve_specification("spec-initial")

        workflow.run_cad({"traceability_id": f"tr_cad_retry_{index}"})
        workflow.start_validation(f"tr_val_retry_{index}")
        result = workflow.handle_validation({"passed": False, "reason_codes": ["RETRY_FAILURE"]})

    assert workflow.state == "escalated_to_human"
    assert result.blocked is True
    assert result.reason == "MAX_REVISION_LOOPS_REACHED"
    assert workflow.failure_count == 3
    assert len(workflow.revision_requests) == 3
    assert all(request["reason_codes"] == ["RETRY_FAILURE"] for request in workflow.revision_requests)


def test_validation_failure_creates_revision_request_with_reason_codes() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.run_cad({"traceability_id": "tr_cad"})
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
    workflow.run_cad({"traceability_id": "tr_cad"})
    workflow.start_validation("tr_val_1")

    for index in range(3):
        result = workflow.handle_validation({"passed": False, "reason_codes": ["RETRY_FAILURE"]})
        if index < 2:
            workflow._transition(SPEC_PENDING_APPROVAL)
            workflow.approve_specification(f"spec_retry_{index}")
            workflow.run_cad({"traceability_id": f"tr_cad_retry_{index}"})
            workflow.start_validation(f"tr_val_retry_{index}")

    assert workflow.state == "escalated_to_human"
    assert result is not None
    assert result.blocked is True
    assert result.reason == "MAX_REVISION_LOOPS_REACHED"
    assert workflow.events[-1]["type"] == "validation_escalated_to_human"


def test_export_blocked_without_validation_pass() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.run_cad({"dsl": "golden"})

    result = workflow.request_export()

    assert result.blocked is True
    assert result.reason == "VALIDATION_NOT_PASSED"


def test_export_blocked_without_export_approval() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.run_cad({"traceability_id": "tr_cad"})
    workflow.start_validation("tr_val_1")
    workflow.handle_validation({"passed": True, "reason_codes": []})

    result = workflow.request_export("tr_val_1")

    assert result.blocked is True
    assert result.reason == "EXPORT_APPROVAL_REQUIRED"


def test_audit_jsonl_records_export_decision(tmp_path):
    workflow = Workflow(audit_path=tmp_path / "audit.jsonl")
    workflow.approve_specification("spec-1")
    workflow.run_cad({"traceability_id": "tr_cad"})
    workflow.start_validation("tr_val_1")
    workflow.handle_validation({"passed": True, "reason_codes": []})
    workflow.request_export("tr_val_1")
    workflow.approve_export("export-1")

    lines = (tmp_path / "audit.jsonl").read_text().splitlines()
    records = [json.loads(line) for line in lines]
    export_events = [record for record in records if "export_approved" in json.dumps(record, ensure_ascii=False)]

    assert len(records) == 6
    assert [record["event_type"] for record in records] == [
        "specification_approved",
        "cad_built",
        "validation_started",
        "validation_passed",
        "export_requested",
        "export_approved",
    ]
    assert any("export_approved" in line for line in lines)
    assert len(export_events) == 1
    assert export_events[0]["event_type"] == "export_approved"
    assert export_events[0]["traceability_id"] == "export-1"
    assert "timestamp" in export_events[0]
    assert export_events[0]["payload"]["decision"]["approval_type"] == "export"


def test_export_approval_moves_workflow_to_exported() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.run_cad({"traceability_id": "tr_cad"})
    workflow.start_validation("tr_val_1")
    workflow.handle_validation({"passed": True, "reason_codes": []})

    request = workflow.request_export("tr_val_1")
    result = workflow.approve_export("export-1")

    assert request.blocked is True
    assert request.reason == "EXPORT_APPROVAL_REQUIRED"
    assert workflow.state == "exported"
    assert result.approved is True
    assert workflow.events[-1]["type"] == "export_approved"
    assert workflow.approval_decisions[-1]["approval_type"] == "export"


def test_cad_generation_blocked_without_spec_approval() -> None:
    workflow = Workflow()

    result = workflow.run_cad({"dsl": "golden"})

    assert result.blocked is True
    assert result.reason == "SPEC_APPROVAL_REQUIRED"
    assert workflow.state == CREATED


def test_cad_generation_allowed_after_spec_approval() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")

    result = workflow.run_cad({"dsl": "golden"})

    assert not result.blocked
    assert workflow.state == "cad_built"


def test_cad_generation_blocked_after_dsl_generation_without_current_spec_approval() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.generate_dsl("tr_dsl")

    result = workflow.run_cad({"dsl": "golden"})

    assert result.blocked is True
    assert result.reason == "SPEC_APPROVAL_REQUIRED"
    assert workflow.state == DSL_GENERATED
    assert workflow.events[-1]["type"] == "dsl_generated"


def test_export_request_blocked_before_validation_passed() -> None:
    workflow = Workflow()

    result = workflow.request_export("tr_export")

    assert result.blocked is True
    assert result.reason == "VALIDATION_NOT_PASSED"
    assert workflow.state == CREATED


def test_export_approval_blocked_without_prior_export_request() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.run_cad({"traceability_id": "tr_cad"})
    workflow.start_validation("tr_val_1")
    workflow.handle_validation({"passed": True, "reason_codes": []})

    with pytest.raises(ValueError, match="invalid workflow transition"):
        workflow.approve_export("export-1")

    assert workflow.state == VALIDATION_PASSED
    assert all(decision["approval_type"] != "export" for decision in workflow.approval_decisions)


def test_validation_pass_blocked_before_cad() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")

    with pytest.raises(ValueError, match="invalid workflow transition"):
        workflow.mark_validation_passed("tr_val_1")

    assert workflow.state == SPEC_APPROVED


def test_mark_validation_passed_from_created_is_rejected() -> None:
    workflow = Workflow()

    with pytest.raises(ValueError, match="invalid workflow transition"):
        workflow.mark_validation_passed("tr_val_1")

    assert workflow.state == CREATED


def test_revision_loop_can_return_to_cad_generation_and_resets_failure_count() -> None:
    workflow = Workflow()
    workflow.approve_specification("spec-1")
    workflow.run_cad({"traceability_id": "tr_cad_1"})
    workflow.start_validation("tr_val_1")
    workflow.handle_validation({"passed": False, "reason_codes": ["RETRY_FAILURE"]})

    workflow._transition(SPEC_PENDING_APPROVAL)
    workflow.approve_specification("spec-2")
    workflow.run_cad({"traceability_id": "tr_cad_2"})
    workflow.start_validation("tr_val_2")
    result = workflow.handle_validation({"passed": True, "reason_codes": []})

    assert workflow.state == VALIDATION_PASSED
    assert result.approved is True
    assert workflow.failure_count == 0
    assert workflow.events[-1]["type"] == "validation_passed"


def test_invalid_state_transition_is_rejected() -> None:
    workflow = Workflow()

    workflow._transition(SPEC_PENDING_APPROVAL)

    try:
        workflow._transition(EXPORTED)
    except ValueError as exc:
        assert "invalid workflow transition" in str(exc)
    else:
        raise AssertionError("invalid transition was accepted")

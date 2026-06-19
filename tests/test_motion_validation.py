from __future__ import annotations

from cad_agent.motion_validation import (
    INSUFFICIENT_CLEARANCE,
    INVALID_ANGULAR_RANGE,
    INVALID_CLEARANCE,
    INVALID_MIN_CLEARANCE,
    MISSING_ANGULAR_RANGE,
    MISSING_CLEARANCE,
    MISSING_MIN_CLEARANCE,
    MISSING_MOVING_PART_IDS,
    MISSING_PART_TRACEABILITY,
    MISSING_ROTATION_AXIS,
    MOVING_PART_ID_NOT_FOUND,
    validate_motion,
)


def valid_motion_state() -> dict[str, object]:
    return {
        "traceability_id": "tr_motion_fixture_valid_1",
        "mechanism_id": "mech_fixture_rotation_1",
        "motion_type": "rotation",
        "rotation_axis": "z",
        "angular_range_deg": {"start_deg": 0.0, "end_deg": 90.0},
        "moving_part_ids": ["rotor"],
        "parts": [{"part_id": "rotor", "traceability_id": "tr_part_rotor_fixture_1"}],
    }


def motion_state_with_clearance(clearance_mm: float, min_clearance_mm: float) -> dict[str, object]:
    state = valid_motion_state()
    state["clearance_mm"] = clearance_mm
    state["min_clearance_mm"] = min_clearance_mm
    return state


def test_missing_rotation_axis_fails() -> None:
    result = validate_motion({"parts": []})

    assert result.valid is False
    assert result.reason_code == MISSING_ROTATION_AXIS
    assert result.report["status"] == "fail"
    assert result.report["reason_codes"][0] == MISSING_ROTATION_AXIS
    assert MISSING_ROTATION_AXIS in result.report["reason_codes"]
    assert "$.rotation_axis" in result.report["failure_locations"]
    assert result.report["analysis_scope"] == "bounded_motion_state_schema_v0"
    assert result.report["traceability_id"].startswith("tr_motion_")


def test_valid_rotation_motion_state_passes() -> None:
    result = validate_motion(valid_motion_state())

    assert result.valid is True
    assert result.reason_code is None
    assert result.report["status"] == "pass"
    assert result.report["overall"] == "pass"
    assert result.report["reason_codes"] == []
    assert result.report["failure_locations"] == []
    assert result.report["checks"] == []
    assert result.report["traceability_id"] == "tr_motion_fixture_valid_1"


def test_insufficient_clearance_fails() -> None:
    state = {"rotation_axis": "z", "clearance_mm": 0.2, "min_clearance_mm": 1.0}

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == INSUFFICIENT_CLEARANCE
    assert result.report["reason_codes"][0] == INSUFFICIENT_CLEARANCE
    assert INSUFFICIENT_CLEARANCE in result.report["reason_codes"]
    assert "$.clearance_mm" in result.report["failure_locations"]


def test_sufficient_clearance_passes() -> None:
    result = validate_motion(motion_state_with_clearance(clearance_mm=2.0, min_clearance_mm=1.0))

    assert result.valid is True
    assert result.reason_code is None
    assert result.report["reason_codes"] == []
    assert result.report["failure_locations"] == []


def test_equal_clearance_passes() -> None:
    result = validate_motion(motion_state_with_clearance(clearance_mm=1.0, min_clearance_mm=1.0))

    assert result.valid is True
    assert result.reason_code is None
    assert result.report["reason_codes"] == []


def test_missing_min_clearance_fails() -> None:
    state = valid_motion_state()
    state["clearance_mm"] = 2.0

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == MISSING_MIN_CLEARANCE
    assert result.report["reason_codes"] == [MISSING_MIN_CLEARANCE]
    assert result.report["failure_locations"] == ["$.min_clearance_mm"]


def test_missing_clearance_fails() -> None:
    state = valid_motion_state()
    state["min_clearance_mm"] = 1.0

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == MISSING_CLEARANCE
    assert result.report["reason_codes"] == [MISSING_CLEARANCE]
    assert result.report["failure_locations"] == ["$.clearance_mm"]


def test_invalid_clearance_fails() -> None:
    state = valid_motion_state()
    state["clearance_mm"] = -0.1
    state["min_clearance_mm"] = 1.0

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == INVALID_CLEARANCE
    assert result.report["reason_codes"] == [INVALID_CLEARANCE]
    assert result.report["failure_locations"] == ["$.clearance_mm"]


def test_invalid_min_clearance_fails() -> None:
    state = valid_motion_state()
    state["clearance_mm"] = 2.0
    state["min_clearance_mm"] = "bad"

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == INVALID_MIN_CLEARANCE
    assert result.report["reason_codes"] == [INVALID_MIN_CLEARANCE]
    assert result.report["failure_locations"] == ["$.min_clearance_mm"]


def test_missing_angular_range_fails() -> None:
    state = valid_motion_state()
    del state["angular_range_deg"]

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == MISSING_ANGULAR_RANGE
    assert result.report["reason_codes"] == [MISSING_ANGULAR_RANGE]
    assert result.report["failure_locations"] == ["$.angular_range_deg"]


def test_invalid_angular_range_fails() -> None:
    state = valid_motion_state()
    state["angular_range_deg"] = {"start_deg": 90, "end_deg": 0}

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == INVALID_ANGULAR_RANGE
    assert result.report["reason_codes"] == [INVALID_ANGULAR_RANGE]


def test_missing_moving_part_ids_fails() -> None:
    state = valid_motion_state()
    del state["moving_part_ids"]

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == MISSING_MOVING_PART_IDS
    assert result.report["reason_codes"] == [MISSING_MOVING_PART_IDS]
    assert result.report["failure_locations"] == ["$.moving_part_ids"]


def test_moving_part_id_not_declared_fails() -> None:
    state = valid_motion_state()
    state["moving_part_ids"] = ["rotor", "missing_rotor"]

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == MOVING_PART_ID_NOT_FOUND
    assert result.report["reason_codes"] == [MOVING_PART_ID_NOT_FOUND]
    assert result.report["failure_locations"] == ["$.moving_part_ids['missing_rotor']"]


def test_part_traceability_is_required_for_declared_parts() -> None:
    state = valid_motion_state()
    state["parts"] = [{"part_id": "rotor"}]

    result = validate_motion(state)

    assert result.valid is False
    assert result.reason_code == MISSING_PART_TRACEABILITY
    assert result.report["reason_codes"] == [MISSING_PART_TRACEABILITY]
    assert result.report["failure_locations"] == ["$.parts[0].traceability_id"]

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any


MISSING_ROTATION_AXIS = "MISSING_ROTATION_AXIS"
INVALID_ROTATION_AXIS = "INVALID_ROTATION_AXIS"
MISSING_ANGULAR_RANGE = "MISSING_ANGULAR_RANGE"
INVALID_ANGULAR_RANGE = "INVALID_ANGULAR_RANGE"
MISSING_MOVING_PART_IDS = "MISSING_MOVING_PART_IDS"
INVALID_MOVING_PART_IDS = "INVALID_MOVING_PART_IDS"
MOVING_PART_ID_NOT_FOUND = "MOVING_PART_ID_NOT_FOUND"
MISSING_PART_ID = "MISSING_PART_ID"
MISSING_PART_TRACEABILITY = "MISSING_PART_TRACEABILITY"
INVALID_PARTS = "INVALID_PARTS"
UNSUPPORTED_MOTION_TYPE = "UNSUPPORTED_MOTION_TYPE"
INVALID_MOTION_STATE = "INVALID_MOTION_STATE"

ALLOWED_ROTATION_AXES = frozenset({"x", "y", "z"})


@dataclass(frozen=True, slots=True)
class MotionValidationResult:
    valid: bool
    reason_code: str | None = None
    report: dict[str, Any] = field(default_factory=dict)


def validate_motion(state: dict[str, Any]) -> MotionValidationResult:
    """Validate the bounded motion-state contract for approved mechanism fixtures.

    Task 08.1 only implements deterministic schema/state checks. Clearance and
    sweep collision rules are explicitly deferred to later CAD-P08 tasks.
    """
    if not isinstance(state, dict):
        return _fail(INVALID_MOTION_STATE, "motion state must be an object", "$", state)

    report = _base_report(state)
    reason_codes: list[str] = []
    failure_locations: list[str] = []

    motion_type = state.get("motion_type", "rotation")
    if motion_type != "rotation":
        reason_codes.append(UNSUPPORTED_MOTION_TYPE)
        failure_locations.append("$.motion_type")

    axis = state.get("rotation_axis")
    if axis is None:
        reason_codes.append(MISSING_ROTATION_AXIS)
        failure_locations.append("$.rotation_axis")
    elif not isinstance(axis, str) or axis not in ALLOWED_ROTATION_AXES:
        reason_codes.append(INVALID_ROTATION_AXIS)
        failure_locations.append("$.rotation_axis")

    angular_range = state.get("angular_range_deg")
    if angular_range is None:
        reason_codes.append(MISSING_ANGULAR_RANGE)
        failure_locations.append("$.angular_range_deg")
    elif not _is_valid_angular_range(angular_range):
        reason_codes.append(INVALID_ANGULAR_RANGE)
        failure_locations.append("$.angular_range_deg")

    moving_part_ids = state.get("moving_part_ids")
    if not _is_non_empty_string_list(moving_part_ids):
        reason_codes.append(MISSING_MOVING_PART_IDS if moving_part_ids is None or moving_part_ids == [] else INVALID_MOVING_PART_IDS)
        failure_locations.append("$.moving_part_ids")
    else:
        parts = state.get("parts", [])
        if parts == []:
            parts = []
        if parts is not None and not isinstance(parts, list):
            reason_codes.append(INVALID_PARTS)
            failure_locations.append("$.parts")
        else:
            part_ids = _part_ids(parts)
            for part_id in moving_part_ids:
                if part_id not in part_ids:
                    reason_codes.append(MOVING_PART_ID_NOT_FOUND)
                    failure_locations.append(f"$.moving_part_ids[{part_id!r}]")
            for index, part in enumerate(parts):
                if not isinstance(part, dict):
                    reason_codes.append(INVALID_PARTS)
                    failure_locations.append(f"$.parts[{index}]")
                    continue
                if not isinstance(part.get("part_id"), str) or part.get("part_id") == "":
                    reason_codes.append(MISSING_PART_ID)
                    failure_locations.append(f"$.parts[{index}].part_id")
                if not isinstance(part.get("traceability_id"), str) or part.get("traceability_id") == "":
                    reason_codes.append(MISSING_PART_TRACEABILITY)
                    failure_locations.append(f"$.parts[{index}].traceability_id")

    valid = not reason_codes
    report.update(
        {
            "valid": valid,
            "status": "pass" if valid else "fail",
            "overall": "pass" if valid else "fail",
            "reason_codes": reason_codes,
            "failure_locations": failure_locations,
            "checks": _checks_from_reason_codes(reason_codes),
            "revision_feedback": _revision_feedback(reason_codes),
        }
    )
    return MotionValidationResult(valid=valid, reason_code=reason_codes[0] if reason_codes else None, report=report)


def _base_report(state: dict[str, Any]) -> dict[str, Any]:
    traceability_id = state.get("traceability_id")
    if not isinstance(traceability_id, str) or traceability_id == "":
        traceability_id = _generated_traceability_id(state)

    mechanism_id = state.get("mechanism_id")
    return {
        "traceability_id": traceability_id,
        "mechanism_id": mechanism_id if isinstance(mechanism_id, str) else None,
        "analysis_scope": "bounded_motion_state_schema_v0",
        "valid": False,
        "status": "fail",
        "overall": "fail",
        "reason_codes": [],
        "failure_locations": [],
        "checks": [],
        "revision_feedback": [],
    }


def _checks_from_reason_codes(reason_codes: list[str]) -> list[dict[str, Any]]:
    check_names = {
        MISSING_ROTATION_AXIS: "rotation_axis_check",
        INVALID_ROTATION_AXIS: "rotation_axis_check",
        MISSING_ANGULAR_RANGE: "angular_range_check",
        INVALID_ANGULAR_RANGE: "angular_range_check",
        MISSING_MOVING_PART_IDS: "moving_part_ids_check",
        INVALID_MOVING_PART_IDS: "moving_part_ids_check",
        MOVING_PART_ID_NOT_FOUND: "moving_part_ids_check",
        MISSING_PART_ID: "part_traceability_check",
        MISSING_PART_TRACEABILITY: "part_traceability_check",
        INVALID_PARTS: "parts_shape_check",
        UNSUPPORTED_MOTION_TYPE: "motion_type_check",
        INVALID_MOTION_STATE: "motion_state_shape_check",
    }
    return [{"name": check_names.get(code, "motion_validation_check"), "status": "fail", "reason_code": code} for code in reason_codes]


def _revision_feedback(reason_codes: list[str]) -> list[dict[str, str]]:
    feedback = {
        MISSING_ROTATION_AXIS: "Add rotation_axis as one of x, y, z.",
        INVALID_ROTATION_AXIS: "Use a supported rotation_axis value: x, y, or z.",
        MISSING_ANGULAR_RANGE: "Add angular_range_deg with numeric start_deg and end_deg values.",
        INVALID_ANGULAR_RANGE: "Ensure angular_range_deg.start_deg and end_deg are finite numbers and end_deg is greater than start_deg.",
        MISSING_MOVING_PART_IDS: "Add a non-empty moving_part_ids array.",
        INVALID_MOVING_PART_IDS: "moving_part_ids must be a non-empty array of non-empty strings.",
        MOVING_PART_ID_NOT_FOUND: "Declare every moving_part_id in parts[].part_id.",
        MISSING_PART_ID: "Every part in parts must include a non-empty part_id.",
        MISSING_PART_TRACEABILITY: "Every part in parts must include a non-empty traceability_id.",
        INVALID_PARTS: "parts must be an array of part objects when provided.",
        UNSUPPORTED_MOTION_TYPE: "Current bounded motion validation supports motion_type=rotation only.",
        INVALID_MOTION_STATE: "Motion state must be a JSON object.",
    }
    return [{"reason_code": code, "message": feedback.get(code, "Revise motion validation input.")} for code in reason_codes]


def _is_valid_angular_range(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    start = value.get("start_deg")
    end = value.get("end_deg")
    return _is_finite_number(start) and _is_finite_number(end) and end > start


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item != "" for item in value)


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _part_ids(parts: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("part_id"), str) and part["part_id"] != "":
                ids.add(part["part_id"])
    return ids


def _generated_traceability_id(state: dict[str, Any]) -> str:
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"tr_motion_{digest}"


def _fail(reason_code: str, message: str, location: str, state: Any) -> MotionValidationResult:
    report = {
        "traceability_id": _generated_traceability_id(state),
        "mechanism_id": None,
        "analysis_scope": "bounded_motion_state_schema_v0",
        "valid": False,
        "status": "fail",
        "overall": "fail",
        "reason_codes": [reason_code],
        "failure_locations": [location],
        "checks": [{"name": "motion_state_shape_check", "status": "fail", "reason_code": reason_code}],
        "revision_feedback": [{"reason_code": reason_code, "message": message}],
    }
    return MotionValidationResult(valid=False, reason_code=reason_code, report=report)

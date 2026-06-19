from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

ALLOWED_DSL_OPERATIONS = frozenset({"box", "cylinder", "through_hole"})
APPROVED_MECHANISM_OPERATIONS = frozenset({"shaft"})
TRACEABILITY_ID_PATTERN = re.compile(r"^tr_dsl_[A-Za-z0-9_]+$")
PARAMETER_REFERENCE_PATTERN = re.compile(r"^\$[A-Za-z_][A-Za-z0-9_]*$")
UNSUPPORTED_MECHANISM_OP = "UNSUPPORTED_MECHANISM_OP"
NEW_OPERATION_APPROVAL_REQUIRED = "NEW_OPERATION_APPROVAL_REQUIRED"
INVALID_MECHANISM_PLAN = "INVALID_MECHANISM_PLAN"
INVALID_PARAMETER_REFERENCE = "INVALID_PARAMETER_REFERENCE"
INVALID_POSITIONS_MM = "INVALID_POSITIONS_MM"
INVALID_FEATURE_SHAPE = "INVALID_FEATURE_SHAPE"


@dataclass(frozen=True, slots=True)
class CompileResult:
    valid: bool
    reason_code: str | None = None
    dsl: dict[str, Any] = field(default_factory=dict)


def compile_mechanism_plan(plan: dict[str, Any]) -> CompileResult:
    """Compile an approved mechanism plan into Phase 1 Parametric DSL.

    Task 06.2 approves a minimal deterministic mechanism operation set for this
    branch: `shaft`. Other mechanism-specific operations remain rejected until a
    later contract update approves them.
    """
    if not isinstance(plan, dict):
        return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)

    operations = plan.get("operations", [])
    if not isinstance(operations, list):
        return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)

    has_mechanism_operation = False
    for operation in operations:
        if not isinstance(operation, dict):
            return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)
        if "code" in operation or "raw_code" in operation:
            return CompileResult(valid=False, reason_code=UNSUPPORTED_MECHANISM_OP)
        op = operation.get("op")
        if op is None:
            return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)
        if op in APPROVED_MECHANISM_OPERATIONS:
            has_mechanism_operation = True
            continue
        if op not in ALLOWED_DSL_OPERATIONS:
            return CompileResult(valid=False, reason_code=NEW_OPERATION_APPROVAL_REQUIRED)

    if has_mechanism_operation:
        return _compile_approved_mechanism_plan(plan, operations)
    return _compile_phase1_passthrough(plan, operations)


def _compile_phase1_passthrough(plan: dict[str, Any], operations: list[Any]) -> CompileResult:
    parameters = plan.get("parameters", {})
    if not isinstance(parameters, dict):
        return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)
    parameter_check = _validate_parameters(parameters)
    if not parameter_check.valid:
        return parameter_check

    features = plan.get("features", operations)
    if not isinstance(features, list) or not features:
        return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)

    feature_check = _validate_phase1_features(features, parameters)
    if not feature_check.valid:
        return feature_check

    dsl = {
        "traceability_id": _schema_valid_traceability_id(plan, "phase1"),
        "units": "mm",
        "parameters": parameters,
        "features": features,
        "derivative_outputs": ["step_ap242"],
    }
    return CompileResult(valid=True, dsl=dsl)


def _compile_approved_mechanism_plan(plan: dict[str, Any], operations: list[Any]) -> CompileResult:
    plan_parameters = plan.get("parameters", {})
    if not isinstance(plan_parameters, dict):
        return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)
    parameter_check = _validate_parameters(plan_parameters)
    if not parameter_check.valid:
        return parameter_check

    parameters: dict[str, float] = {}
    features: list[dict[str, Any]] = []

    for index, operation in enumerate(operations):
        op = operation.get("op")
        if op == "shaft":
            shaft = _compile_shaft(operation, plan_parameters, parameters, index)
            if not shaft.valid:
                return shaft
            features.extend(shaft.dsl["features"])
            parameters.update(shaft.dsl["parameters"])
        elif op in ALLOWED_DSL_OPERATIONS:
            feature_check = _validate_phase1_feature(operation, parameters, index)
            if not feature_check.valid:
                return feature_check
            features.append(operation)

    dsl = {
        "traceability_id": _schema_valid_traceability_id(plan, "shaft"),
        "units": "mm",
        "parameters": parameters,
        "features": features,
        "derivative_outputs": ["step_ap242"],
    }
    return CompileResult(valid=True, dsl=dsl)


def _compile_shaft(
    operation: dict[str, Any],
    plan_parameters: dict[str, Any],
    generated_parameters: dict[str, float],
    index: int,
) -> CompileResult:
    suffix = "" if len(generated_parameters) == 0 else f"_{index}"
    radius_name = f"radius{suffix}"
    length_name = f"length{suffix}"

    diameter = _resolve_dimension(operation, "diameter_mm", plan_parameters, generated_parameters, radius_name, allow_direct_number=True)
    if not diameter.valid:
        return diameter
    length = _resolve_dimension(operation, "length_mm", plan_parameters, generated_parameters, length_name, allow_direct_number=True)
    if not length.valid:
        return length

    positions_mm = operation.get("positions_mm", [[0, 0]])
    if not _is_valid_positions_mm(positions_mm):
        return CompileResult(valid=False, reason_code=INVALID_POSITIONS_MM)

    radius = diameter.dsl["value"] / 2.0
    generated_parameters = {radius_name: radius, length_name: length.dsl["value"]}
    feature = {
        "op": "cylinder",
        "radius_mm": f"${radius_name}",
        "height_mm": f"${length_name}",
        "axis": "z",
        "positions_mm": positions_mm,
    }
    return CompileResult(valid=True, dsl={"parameters": generated_parameters, "features": [feature]})


def _validate_phase1_features(features: list[Any], parameters: dict[str, Any]) -> CompileResult:
    for index, feature in enumerate(features):
        check = _validate_phase1_feature(feature, parameters, index)
        if not check.valid:
            return check
    return CompileResult(valid=True)


def _validate_phase1_feature(feature: Any, parameters: dict[str, Any], index: int) -> CompileResult:
    if not isinstance(feature, dict):
        return CompileResult(valid=False, reason_code=INVALID_FEATURE_SHAPE)

    op = feature.get("op")
    if op is None:
        return CompileResult(valid=False, reason_code=INVALID_FEATURE_SHAPE)
    if op not in ALLOWED_DSL_OPERATIONS:
        return CompileResult(valid=False, reason_code=NEW_OPERATION_APPROVAL_REQUIRED)

    if op == "box":
        required = {"length_mm", "width_mm", "height_mm"}
    elif op == "cylinder":
        required = {"radius_mm", "height_mm", "axis", "positions_mm"}
    else:
        required = {"axis", "diameter_mm", "depth_mm", "positions_mm"}

    missing = sorted(required - set(feature))
    if missing:
        return CompileResult(valid=False, reason_code=INVALID_FEATURE_SHAPE)

    axis = feature.get("axis")
    if axis is not None and axis != "z":
        return CompileResult(valid=False, reason_code=INVALID_FEATURE_SHAPE)

    if "positions_mm" in feature and not _is_valid_positions_mm(feature["positions_mm"]):
        return CompileResult(valid=False, reason_code=INVALID_POSITIONS_MM)

    dimension_keys = sorted(required & {"length_mm", "width_mm", "height_mm", "radius_mm", "diameter_mm", "depth_mm"})
    for key in dimension_keys:
        check = _resolve_dimension(feature, key, parameters, {}, f"feature_{index}_{key}")
        if not check.valid:
            return check

    return CompileResult(valid=True)


def _resolve_dimension(
    operation: dict[str, Any],
    key: str,
    plan_parameters: dict[str, Any],
    generated_parameters: dict[str, float],
    parameter_name: str,
    allow_direct_number: bool = False,
) -> CompileResult:
    del parameter_name
    value = operation.get(key)
    if isinstance(value, bool) or value is None:
        return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)
    if isinstance(value, (int, float)):
        if allow_direct_number:
            return CompileResult(valid=True, dsl={"value": float(value)})
        return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)
    if not isinstance(value, str) or not PARAMETER_REFERENCE_PATTERN.fullmatch(value):
        return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)

    name = value[1:]
    if name in generated_parameters:
        resolved = generated_parameters[name]
    elif name in plan_parameters:
        resolved = plan_parameters[name]
    else:
        return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)

    if isinstance(resolved, bool) or not isinstance(resolved, (int, float)):
        return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)
    return CompileResult(valid=True, dsl={"value": float(resolved)})


def _validate_parameters(parameters: dict[str, Any]) -> CompileResult:
    for name, value in parameters.items():
        if not isinstance(name, str) or not PARAMETER_REFERENCE_PATTERN.fullmatch(f"${name}"):
            return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)
    return CompileResult(valid=True)


def _is_valid_positions_mm(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for coordinate_pair in value:
        if not isinstance(coordinate_pair, list) or len(coordinate_pair) != 2:
            return False
        for coordinate in coordinate_pair:
            if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
                return False
    return True


def _schema_valid_traceability_id(plan: dict[str, Any], fallback_prefix: str) -> str:
    traceability_id = plan.get("traceability_id")
    if isinstance(traceability_id, str) and TRACEABILITY_ID_PATTERN.fullmatch(traceability_id):
        return traceability_id
    source = traceability_id if isinstance(traceability_id, str) else str(traceability_id)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
    return f"tr_dsl_{fallback_prefix}_{digest}"


__all__ = [
    "ALLOWED_DSL_OPERATIONS",
    "APPROVED_MECHANISM_OPERATIONS",
    "CompileResult",
    "INVALID_FEATURE_SHAPE",
    "INVALID_MECHANISM_PLAN",
    "INVALID_PARAMETER_REFERENCE",
    "INVALID_POSITIONS_MM",
    "NEW_OPERATION_APPROVAL_REQUIRED",
    "UNSUPPORTED_MECHANISM_OP",
    "compile_mechanism_plan",
]

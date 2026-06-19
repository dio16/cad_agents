from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ALLOWED_DSL_OPERATIONS = frozenset({"box", "cylinder", "through_hole"})
APPROVED_MECHANISM_OPERATIONS = frozenset({"shaft"})
UNSUPPORTED_MECHANISM_OP = "UNSUPPORTED_MECHANISM_OP"
INVALID_MECHANISM_PLAN = "INVALID_MECHANISM_PLAN"
INVALID_PARAMETER_REFERENCE = "INVALID_PARAMETER_REFERENCE"


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
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)
        if "code" in operation or "raw_code" in operation:
            return CompileResult(valid=False, reason_code=UNSUPPORTED_MECHANISM_OP)
        op = operation.get("op")
        if op in APPROVED_MECHANISM_OPERATIONS:
            has_mechanism_operation = True
            continue
        if op not in ALLOWED_DSL_OPERATIONS:
            return CompileResult(valid=False, reason_code=UNSUPPORTED_MECHANISM_OP)

    if has_mechanism_operation:
        return _compile_approved_mechanism_plan(plan, operations)
    return _compile_phase1_passthrough(plan, operations)


def _compile_phase1_passthrough(plan: dict[str, Any], operations: list[Any]) -> CompileResult:
    traceability_id = plan.get("traceability_id") or "tr_dsl_mechanism"
    parameters = plan.get("parameters", {})
    features = plan.get("features", operations)
    derivative_outputs = plan.get("derivative_outputs", ["step_ap242"])

    dsl = {
        "traceability_id": str(traceability_id),
        "units": "mm",
        "parameters": parameters if isinstance(parameters, dict) else {},
        "features": features if isinstance(features, list) else [],
        "derivative_outputs": derivative_outputs if isinstance(derivative_outputs, list) else ["step_ap242"],
        "compiler": {
            "phase": "CAD-P06.2",
            "allowlist": sorted(ALLOWED_DSL_OPERATIONS),
            "approved_mechanism_operations": sorted(APPROVED_MECHANISM_OPERATIONS),
            "mechanism_operations_accepted": False,
        },
    }
    return CompileResult(valid=True, dsl=dsl)


def _compile_approved_mechanism_plan(plan: dict[str, Any], operations: list[Any]) -> CompileResult:
    parameters: dict[str, float] = {}
    features: list[dict[str, Any]] = []

    for index, operation in enumerate(operations):
        op = operation.get("op")
        if op == "shaft":
            shaft = _compile_shaft(operation, parameters, index)
            if not shaft.valid:
                return shaft
            features.extend(shaft.dsl["features"])
            parameters.update(shaft.dsl["parameters"])
        elif op in ALLOWED_DSL_OPERATIONS:
            features.append(operation)

    traceability_id = plan.get("traceability_id") or "tr_dsl_mechanism"
    dsl = {
        "traceability_id": str(traceability_id),
        "units": "mm",
        "parameters": parameters,
        "features": features,
        "derivative_outputs": ["step_ap242"],
        "compiler": {
            "phase": "CAD-P06.2",
            "allowlist": sorted(ALLOWED_DSL_OPERATIONS),
            "approved_mechanism_operations": sorted(APPROVED_MECHANISM_OPERATIONS),
            "mechanism_operations_accepted": True,
        },
    }
    return CompileResult(valid=True, dsl=dsl)


def _compile_shaft(operation: dict[str, Any], parameters: dict[str, float], index: int) -> CompileResult:
    suffix = "" if len(parameters) == 0 else f"_{index}"
    radius_name = f"radius{suffix}"
    length_name = f"length{suffix}"

    diameter = _resolve_dimension(operation, "diameter_mm", parameters)
    if not diameter.valid:
        return diameter
    length = _resolve_dimension(operation, "length_mm", parameters)
    if not length.valid:
        return length

    radius = diameter.dsl["value"] / 2.0
    generated_parameters = {radius_name: radius, length_name: length.dsl["value"]}
    feature = {
        "op": "cylinder",
        "radius_mm": f"${radius_name}",
        "height_mm": f"${length_name}",
        "axis": "z",
        "positions_mm": operation.get("positions_mm", [[0, 0]]),
    }
    return CompileResult(valid=True, dsl={"parameters": generated_parameters, "features": [feature]})


def _resolve_dimension(
    operation: dict[str, Any],
    key: str,
    parameters: dict[str, float],
) -> CompileResult:
    value = operation.get(key)
    if isinstance(value, bool) or value is None:
        return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)
    if isinstance(value, (int, float)):
        return CompileResult(valid=True, dsl={"value": float(value)})
    if isinstance(value, str) and value.startswith("$"):
        name = value[1:]
        if name not in parameters:
            return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)
        resolved = parameters[name]
        if isinstance(resolved, bool) or not isinstance(resolved, (int, float)):
            return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)
        return CompileResult(valid=True, dsl={"value": float(resolved)})
    try:
        return CompileResult(valid=True, dsl={"value": float(value)})
    except (TypeError, ValueError):
        return CompileResult(valid=False, reason_code=INVALID_PARAMETER_REFERENCE)


__all__ = [
    "ALLOWED_DSL_OPERATIONS",
    "APPROVED_MECHANISM_OPERATIONS",
    "CompileResult",
    "INVALID_MECHANISM_PLAN",
    "INVALID_PARAMETER_REFERENCE",
    "UNSUPPORTED_MECHANISM_OP",
    "compile_mechanism_plan",
]

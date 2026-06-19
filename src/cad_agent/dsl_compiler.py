from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ALLOWED_DSL_OPERATIONS = frozenset({"box", "cylinder", "through_hole"})
UNSUPPORTED_MECHANISM_OP = "UNSUPPORTED_MECHANISM_OP"
INVALID_MECHANISM_PLAN = "INVALID_MECHANISM_PLAN"


@dataclass(frozen=True, slots=True)
class CompileResult:
    valid: bool
    reason_code: str | None = None
    dsl: dict[str, Any] = field(default_factory=dict)


def compile_mechanism_plan(plan: dict[str, Any]) -> CompileResult:
    """Compile a mechanism plan into Phase 1 Parametric DSL when allowlisted.

    Task 06.1 is intentionally limited to defining and enforcing the current
    Phase 1 allowlist. Mechanism-specific operations remain future contract work.
    """
    if not isinstance(plan, dict):
        return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)

    operations = plan.get("operations", [])
    if not isinstance(operations, list):
        return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)

    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            return CompileResult(valid=False, reason_code=INVALID_MECHANISM_PLAN)
        op = operation.get("op")
        if op not in ALLOWED_DSL_OPERATIONS:
            return CompileResult(valid=False, reason_code=UNSUPPORTED_MECHANISM_OP)
        if "code" in operation or "raw_code" in operation:
            return CompileResult(valid=False, reason_code=UNSUPPORTED_MECHANISM_OP)

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
            "phase": "CAD-P06.1",
            "allowlist": sorted(ALLOWED_DSL_OPERATIONS),
            "mechanism_operations_accepted": False,
        },
    }
    return CompileResult(valid=True, dsl=dsl)


__all__ = [
    "ALLOWED_DSL_OPERATIONS",
    "CompileResult",
    "INVALID_MECHANISM_PLAN",
    "UNSUPPORTED_MECHANISM_OP",
    "compile_mechanism_plan",
]

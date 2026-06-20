from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .common import AgentRouteResult, failure, retry_schema, success, write_agent_route_audit

REQUIRED_SPECIFICATION_FIELDS = {
    "traceability_id",
    "requirement_id",
    "parameter_table",
    "constraints",
    "material_candidates",
    "manufacturing_profile",
    "validation_plan",
    "unresolved_risks",
}


def compose_specification(
    requirement: dict[str, Any] | str | None = None,
    attempts: Iterable[str | dict[str, Any]] | None = None,
    max_retries: int = 2,
    **metadata: Any,
) -> AgentRouteResult:
    """Compose a deterministic Phase 1 Specification JSON fixture."""
    audit_path = metadata.pop("audit_path", None)
    if attempts is not None:
        result = retry_schema(attempts, max_retries=max_retries, validator=_has_required_specification_fields, **metadata)
        write_agent_route_audit(result, audit_path)
        return result

    if requirement is not None and not isinstance(requirement, (dict, str)):
        result = failure("INVALID_AGENT_INPUT", "spec_composer", "requirement must be text or structured JSON", **metadata)
        write_agent_route_audit(result, audit_path)
        return result

    requirement_id = _requirement_id(requirement)
    result = success(specification_fixture(requirement_id=requirement_id), "spec_composer", **metadata)
    write_agent_route_audit(result, audit_path)
    return result


def specification_fixture(requirement_id: str = "tr_req_agent_fixture") -> dict[str, Any]:
    return {
        "traceability_id": "tr_spec_agent_fixture",
        "requirement_id": requirement_id,
        "parameter_table": {"length": 64.0, "width": 32.0, "height": 8.0, "wall_t": 4.0, "hole_d": 4.3, "hole_pitch": 42.0},
        "constraints": ["wall_t >= 2.0", "hole_d >= 3.0", "units == mm"],
        "material_candidates": ["PLA", "PETG"],
        "manufacturing_profile": "fdm_standard",
        "validation_plan": ["dimensions_check", "topology_check", "unit_consistency", "manufacturing_profile_rules"],
        "unresolved_risks": ["service temperature unknown"],
    }


def _has_required_specification_fields(document: dict[str, Any]) -> bool:
    return REQUIRED_SPECIFICATION_FIELDS.issubset(document)


def _requirement_id(requirement: dict[str, Any] | str | None) -> str:
    if isinstance(requirement, dict):
        requirement_id = requirement.get("traceability_id")
        return requirement_id if isinstance(requirement_id, str) and requirement_id.startswith("tr_req_") else "tr_req_agent_fixture"
    return "tr_req_agent_fixture"

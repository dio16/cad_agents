from __future__ import annotations

from typing import Any

from .common import AgentRouteResult, failure, success, write_agent_route_audit


def plan_mechanism(requirement: dict[str, Any] | str | None = None, **metadata: Any) -> AgentRouteResult:
    """Return a deterministic bounded mechanism plan fixture."""
    audit_path = metadata.pop("audit_path", None)
    if requirement is not None and not isinstance(requirement, (dict, str)):
        result = failure("INVALID_AGENT_INPUT", "mechanism_planner", "requirement must be text or structured JSON", **metadata)
        write_agent_route_audit(result, audit_path)
        return result

    result = success(mechanism_plan_fixture(requirement=requirement), "mechanism_planner", **metadata)
    write_agent_route_audit(result, audit_path)
    return result


def mechanism_plan_fixture(requirement: dict[str, Any] | str | None = None) -> dict[str, Any]:
    requirement_id = _requirement_id(requirement)
    return {
        "traceability_id": "tr_mech_agent_fixture",
        "requirement_id": requirement_id,
        "operations": [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}],
    }


def _requirement_id(requirement: dict[str, Any] | str | None) -> str:
    if isinstance(requirement, dict):
        requirement_id = requirement.get("traceability_id")
        return requirement_id if isinstance(requirement_id, str) and requirement_id.startswith("tr_req_") else "tr_req_agent_fixture"
    return "tr_req_agent_fixture"

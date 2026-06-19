from __future__ import annotations

from typing import Any

from .common import AgentRouteResult, failure, success


def compose_specification(requirement: dict[str, Any] | str | None = None, **metadata: Any) -> AgentRouteResult:
    """Compose a deterministic Phase 1 Specification JSON fixture."""
    if requirement is not None and not isinstance(requirement, (dict, str)):
        return failure("INVALID_AGENT_INPUT", "spec_composer", "requirement must be text or structured JSON", **metadata)

    requirement_id = _requirement_id(requirement)
    return success(specification_fixture(requirement_id=requirement_id), "spec_composer", **metadata)


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


def _requirement_id(requirement: dict[str, Any] | str | None) -> str:
    if isinstance(requirement, dict):
        requirement_id = requirement.get("traceability_id")
        return requirement_id if isinstance(requirement_id, str) and requirement_id.startswith("tr_req_") else "tr_req_agent_fixture"
    return "tr_req_agent_fixture"

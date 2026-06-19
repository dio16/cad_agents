from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .common import AgentRouteResult, failure, retry_schema, success

REQUIRED_REQUIREMENT_FIELDS = {
    "traceability_id",
    "product_type",
    "functional_requirements",
    "dimensions",
    "manufacturing",
    "unknowns",
    "assumptions",
}


def extract_requirement(
    input_text: str | dict[str, Any] | None = None,
    attempts: Iterable[str | dict[str, Any]] | None = None,
    max_retries: int = 2,
    **metadata: Any,
) -> AgentRouteResult:
    """Extract a deterministic Phase 1 Requirement JSON fixture.

    This is a bounded local/mock LLM-agent route. It does not call external model
    endpoints and does not execute user-provided code.
    """
    if attempts is not None:
        return retry_schema(attempts, max_retries=max_retries, validator=_has_required_requirement_fields, **metadata)

    if isinstance(input_text, dict):
        missing = sorted(REQUIRED_REQUIREMENT_FIELDS - set(input_text))
        if missing:
            return failure("INVALID_AGENT_INPUT", "requirement_extractor", f"missing requirement fields: {', '.join(missing)}", **metadata)
        return success(dict(input_text), "requirement_extractor", **metadata)

    if not isinstance(input_text, str) or not input_text.strip():
        return failure("INVALID_AGENT_INPUT", "requirement_extractor", "requirement input must be non-empty text or structured JSON", **metadata)

    return success(requirement_fixture(), "requirement_extractor", input_kind="human_text", **metadata)


def _has_required_requirement_fields(document: dict[str, Any]) -> bool:
    return REQUIRED_REQUIREMENT_FIELDS.issubset(document)


def requirement_fixture() -> dict[str, Any]:
    return {
        "traceability_id": "tr_req_agent_fixture",
        "product_type": "single_part",
        "functional_requirements": [
            "hold a 25 mm pipe against a flat mounting surface",
            "provide two screw holes",
        ],
        "dimensions": {
            "length_mm": 64.0,
            "width_mm": 32.0,
            "height_mm": 8.0,
            "pipe_outer_diameter_mm": 25.0,
        },
        "manufacturing": {"primary_process": "FDM", "printer_class": "desktop"},
        "unknowns": ["service temperature", "applied clamp load"],
        "assumptions": ["PLA or PETG prototype", "non-safety-critical fixture"],
    }

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .common import AgentRouteResult, failure, retry_schema, success, write_agent_route_audit

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
    audit_path = metadata.pop("audit_path", None)
    if attempts is not None:
        result = retry_schema(attempts, max_retries=max_retries, validator=_has_required_requirement_fields, **metadata)
        write_agent_route_audit(result, audit_path)
        return result

    if isinstance(input_text, dict):
        missing = sorted(REQUIRED_REQUIREMENT_FIELDS - set(input_text))
        if missing:
            result = failure("INVALID_AGENT_INPUT", "requirement_extractor", f"missing requirement fields: {', '.join(missing)}", **metadata)
            write_agent_route_audit(result, audit_path)
            return result
        result = success(dict(input_text), "requirement_extractor", **metadata)
        write_agent_route_audit(result, audit_path)
        return result

    if not isinstance(input_text, str) or not input_text.strip():
        result = failure("INVALID_AGENT_INPUT", "requirement_extractor", "requirement input must be non-empty text or structured JSON", **metadata)
        write_agent_route_audit(result, audit_path)
        return result

    result = success(requirement_fixture(), "requirement_extractor", input_kind="human_text", **metadata)
    write_agent_route_audit(result, audit_path)
    return result


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


def extract_requirement_llm(
    input_text: str,
    data_classification: str = "internal",
    requested_route: str | None = None,
    traceability_id: str = "",
    audit_path: str | None = None,
) -> AgentRouteResult:
    """Extract a Requirement JSON using the LLM adapter (mock or live).

    In mock mode (default), returns fixture. In live mode (CAD_AGENT_LLM_LIVE=1),
    calls the configured LLM endpoint with routing enforcement.
    """
    from cad_agent.llm_adapter import LLMAdapter

    adapter = LLMAdapter(audit_path=audit_path)
    result = adapter.extract_requirement(
        input_text=input_text,
        data_classification=data_classification,
        requested_route=requested_route,
        traceability_id=traceability_id,
    )
    if not result.valid:
        return failure(
            result.reason_code or "LLM_EXTRACTION_FAILED",
            "requirement_extractor_llm",
            result.detail or "LLM extraction failed",
            model_routing=result.model_routing,
            traceability_id=traceability_id,
        )
    return success(
        result.json,
        "requirement_extractor_llm",
        model_routing=result.model_routing,
        attempt_count=result.attempt_count,
        traceability_id=result.json.get("traceability_id", traceability_id),
    )

from __future__ import annotations

from typing import Any

from cad_agent.phase2_pilot import MODEL_GATEWAY_RULES

CAD_AGENT_API_KEY = "local-dev-key"


def check_api_key(headers: dict[Any, Any]) -> bool:
    for key, value in headers.items():
        normalized_key = str(key).replace("_", "-").lower()
        if normalized_key == "x-api-key":
            return str(value) == CAD_AGENT_API_KEY
    return False


def get_data_classification(project: dict[str, Any] | None) -> str:
    if not isinstance(project, dict):
        return "internal"
    classification = project.get("data_classification")
    return classification if isinstance(classification, str) and classification else "internal"


def check_classification_allowed(classification: str, route: str) -> bool:
    rule = MODEL_GATEWAY_RULES.get(classification)
    if not isinstance(rule, dict):
        return False
    allowed_routes = rule.get("allowed_routes")
    return isinstance(allowed_routes, list) and route in allowed_routes


def is_allowed_raw_code(payload: dict[str, Any]) -> bool:
    return "allow_raw_code" not in payload or payload.get("allow_raw_code") is False

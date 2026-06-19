from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from cad_agent.phase2_pilot import MODEL_GATEWAY_RULES

CAD_AGENT_API_KEY = "local-dev-key"
ROUTE_APPROVAL_REQUIRED = "ROUTE_APPROVAL_REQUIRED"
ROUTE_NOT_ALLOWED = "ROUTE_NOT_ALLOWED"
UNKNOWN_DATA_CLASSIFICATION = "UNKNOWN_DATA_CLASSIFICATION"
SENSITIVE_CLASSIFICATIONS = frozenset({"confidential", "regulated", "export-controlled"})


@dataclass(frozen=True, slots=True)
class ModelRouteDecision:
    allowed: bool
    requires_approval: bool
    data_classification: str
    requested_route: str | None
    selected_route: str
    reason_code: str | None = None
    allowed_routes: tuple[str, ...] = ()
    approval_granted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


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


def route_model(
    data_classification: str,
    requested_route: str | None = None,
    approval_granted: bool = False,
) -> ModelRouteDecision:
    """Return a deterministic local model routing decision.

    Sensitive classifications may not use disallowed commercial routes. Regulated
    and export-controlled routes require human approval even when the selected
    route is otherwise allowed.
    """
    rule = MODEL_GATEWAY_RULES.get(data_classification)
    if not isinstance(rule, dict):
        return ModelRouteDecision(
            allowed=False,
            requires_approval=False,
            data_classification=data_classification,
            requested_route=requested_route,
            selected_route="",
            reason_code=UNKNOWN_DATA_CLASSIFICATION,
        )

    allowed_routes = tuple(str(route) for route in rule.get("allowed_routes", []))
    default_route = str(rule.get("default_route", ""))
    selected_route = requested_route if requested_route is not None else default_route
    route_allowed = selected_route in allowed_routes
    human_approval_required = bool(rule.get("human_approval_required", False))
    requires_approval = human_approval_required or (not route_allowed and data_classification in SENSITIVE_CLASSIFICATIONS)

    if not route_allowed:
        reason_code = ROUTE_APPROVAL_REQUIRED if requires_approval else ROUTE_NOT_ALLOWED
        return ModelRouteDecision(
            allowed=False,
            requires_approval=requires_approval,
            data_classification=data_classification,
            requested_route=requested_route,
            selected_route=default_route,
            reason_code=reason_code,
            allowed_routes=allowed_routes,
            approval_granted=approval_granted,
        )

    if requires_approval and not approval_granted:
        return ModelRouteDecision(
            allowed=False,
            requires_approval=True,
            data_classification=data_classification,
            requested_route=requested_route,
            selected_route=selected_route,
            reason_code=ROUTE_APPROVAL_REQUIRED,
            allowed_routes=allowed_routes,
            approval_granted=False,
        )

    return ModelRouteDecision(
        allowed=True,
        requires_approval=requires_approval,
        data_classification=data_classification,
        requested_route=requested_route,
        selected_route=selected_route,
        reason_code=None,
        allowed_routes=allowed_routes,
        approval_granted=approval_granted,
    )


def is_allowed_raw_code(payload: dict[str, Any]) -> bool:
    return "allow_raw_code" not in payload or payload.get("allow_raw_code") is False


__all__ = [
    "CAD_AGENT_API_KEY",
    "ModelRouteDecision",
    "ROUTE_APPROVAL_REQUIRED",
    "ROUTE_NOT_ALLOWED",
    "UNKNOWN_DATA_CLASSIFICATION",
    "check_api_key",
    "check_classification_allowed",
    "get_data_classification",
    "is_allowed_raw_code",
    "route_model",
]

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentRouteResult:
    valid: bool
    json: dict[str, Any] = field(default_factory=dict)
    reason_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def route_metadata(route: str, **extra: Any) -> dict[str, Any]:
    return {"route": route, "deterministic": True, "model": "local_fixture", **extra}


def success(json_data: dict[str, Any], route: str, **extra: Any) -> AgentRouteResult:
    return AgentRouteResult(valid=True, json=json_data, metadata=route_metadata(route, **extra))


def failure(reason_code: str, route: str, message: str, **extra: Any) -> AgentRouteResult:
    return AgentRouteResult(
        valid=False,
        reason_code=reason_code,
        metadata=route_metadata(route, error=message, **extra),
    )

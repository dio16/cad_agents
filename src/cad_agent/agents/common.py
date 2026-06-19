from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_RETRY_EXHAUSTED = "SCHEMA_RETRY_EXHAUSTED"


@dataclass(frozen=True, slots=True)
class AgentRouteResult:
    valid: bool
    json: dict[str, Any] = field(default_factory=dict)
    reason_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def route_metadata(
    route: str,
    data_classification: str | None = None,
    model_route: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    metadata = {"route": route, "deterministic": True, "model": "local_fixture", **extra}
    if data_classification is not None:
        metadata["data_classification"] = data_classification
    if model_route is not None:
        metadata["model_route"] = model_route
    if data_classification is not None or model_route is not None:
        from cad_agent.security_policy import route_model as route_model_decision

        metadata["model_routing"] = asdict(route_model_decision(data_classification or "internal", model_route))
    return metadata


def success(json_data: dict[str, Any], route: str, **extra: Any) -> AgentRouteResult:
    return AgentRouteResult(valid=True, json=json_data, metadata=route_metadata(route, **extra))


def failure(reason_code: str, route: str, message: str, **extra: Any) -> AgentRouteResult:
    return AgentRouteResult(
        valid=False,
        reason_code=reason_code,
        metadata=route_metadata(route, error=message, **extra),
    )


def write_agent_route_audit(result: AgentRouteResult, audit_path: str | Path | None) -> None:
    if audit_path is None:
        return
    path = Path(audit_path)
    metadata = result.metadata
    model_routing = metadata.get("model_routing", {})
    attempt_count = int(metadata.get("attempt_count", 0) or 0)
    timestamp = datetime.now(timezone.utc)
    event = {
        "event_id": f"evt_{timestamp.strftime('%Y%m%d%H%M%S%f')}",
        "recorded_at": timestamp.isoformat(),
        "event_type": "agent_route_decision",
        "route": metadata.get("route"),
        "data_classification": metadata.get("data_classification", "internal"),
        "model_route": metadata.get("model_route") or model_routing.get("selected_route"),
        "model_routing": model_routing,
        "retry_count": max(0, attempt_count - 1),
        "schema_status": "pass" if result.valid else "fail",
        "valid": result.valid,
        "reason_code": result.reason_code,
        "traceability_id": _traceability_id(result.json),
        "retention_days": 365,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _traceability_id(document: dict[str, Any]) -> str | None:
    value = document.get("traceability_id") if isinstance(document, dict) else None
    return value if isinstance(value, str) else None


def retry_schema(
    attempts: Iterable[str | dict[str, Any]],
    max_retries: int = 2,
    validator: Callable[[dict[str, Any]], bool | AgentRouteResult] | None = None,
    route: str = "schema_retry",
) -> AgentRouteResult:
    """Retry JSON/schema validation with a deterministic local attempt list.

    Each attempt is parsed and validated before the next attempt is considered.
    The function stops at the first valid object or after `max_retries` attempts.
    """
    max_attempts = max(1, int(max_retries))
    errors: list[str] = []

    for index, attempt in enumerate(attempts, start=1):
        if index > max_attempts:
            break
        parsed, error = _parse_attempt(attempt)
        if error is not None:
            errors.append(f"attempt {index}: {error}")
            continue
        if validator is not None:
            validation = validator(parsed)
            if validation is True:
                return success(parsed, route, attempt_count=index, max_retries=max_attempts)
            if isinstance(validation, AgentRouteResult):
                if validation.valid:
                    return success(parsed, route, attempt_count=index, max_retries=max_attempts)
                errors.append(f"attempt {index}: {validation.reason_code or 'SCHEMA_VALIDATION_FAILED'}")
                continue
            if bool(validation):
                return success(parsed, route, attempt_count=index, max_retries=max_attempts)
            errors.append(f"attempt {index}: SCHEMA_VALIDATION_FAILED")
            continue
        return success(parsed, route, attempt_count=index, max_retries=max_attempts)

    return AgentRouteResult(
        valid=False,
        reason_code=SCHEMA_RETRY_EXHAUSTED,
        metadata=route_metadata(route, max_retries=max_attempts, attempt_count=len(errors), errors=errors),
    )


def _parse_attempt(attempt: str | dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(attempt, dict):
        return attempt, None
    if not isinstance(attempt, str):
        return None, "attempt must be JSON text or object"
    try:
        parsed = json.loads(attempt)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(parsed, dict):
        return None, "parsed JSON must be an object"
    return parsed, None


__all__ = [
    "AgentRouteResult",
    "SCHEMA_RETRY_EXHAUSTED",
    "failure",
    "retry_schema",
    "route_metadata",
    "success",
    "write_agent_route_audit",
]

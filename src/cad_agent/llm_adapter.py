"""LLM adapter — deterministic local/mock LLM client with routing enforcement.

Live calls are opt-in via CAD_AGENT_LLM_LIVE=1 env var. CI default = off.
All calls enforce route_model before any external request.
Sensitive data never falls back from onprem to commercial.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .security_policy import (
    ModelRouteDecision,
    ROUTE_APPROVAL_REQUIRED,
    SENSITIVE_CLASSIFICATIONS,
    route_model,
)

LLM_LIVE = os.environ.get("CAD_AGENT_LLM_LIVE", "0") == "1"
DEFAULT_MODEL = "local_fixture"
DEFAULT_TEMPERATURE = 0.0
MAX_RETRIES = 2


@dataclass
class LLMCallResult:
    """Result of a single LLM call attempt."""

    json: dict[str, Any] = field(default_factory=dict)
    valid: bool = False
    reason_code: str | None = None
    detail: str | None = None
    model_routing: dict[str, Any] = field(default_factory=dict)
    attempt_count: int = 0


class LLMAdapter:
    """Deterministic local/mock LLM client with routing enforcement.

    In mock mode (default), returns fixture responses based on agent route.
    In live mode (CAD_AGENT_LLM_LIVE=1), makes real HTTP requests with
    enforcement of route_model policy.
    """

    def __init__(self, audit_path: Path | str | None = None) -> None:
        self._audit_path = Path(audit_path) if audit_path else None

    def extract_requirement(
        self,
        input_text: str,
        data_classification: str = "internal",
        requested_route: str | None = None,
        traceability_id: str = "",
    ) -> LLMCallResult:
        """Call LLM to extract a Requirement JSON from natural language text.

        Enforces route_model. Returns fixture in mock mode.
        """
        return self._call(
            agent_route="requirement_extractor",
            input_text=input_text,
            data_classification=data_classification,
            requested_route=requested_route,
            traceability_id=traceability_id,
        )

    def compose_specification(
        self,
        requirement: dict[str, Any],
        data_classification: str = "internal",
        requested_route: str | None = None,
        traceability_id: str = "",
    ) -> LLMCallResult:
        """Call LLM to compose a Specification JSON from a requirement.

        Enforces route_model. Returns fixture in mock mode.
        """
        return self._call(
            agent_route="spec_composer",
            input_text=json.dumps(requirement),
            data_classification=data_classification,
            requested_route=requested_route,
            traceability_id=traceability_id,
        )

    def _call(
        self,
        agent_route: str,
        input_text: str,
        data_classification: str = "internal",
        requested_route: str | None = None,
        traceability_id: str = "",
    ) -> LLMCallResult:
        # ── Step 1: Routing decision ─────────────────────────────────
        routing = route_model(data_classification, requested_route)
        routing_dict = routing.as_dict()

        if not routing.allowed:
            return LLMCallResult(
                valid=False,
                reason_code=routing.reason_code or "ROUTE_NOT_ALLOWED",
                detail=f"model routing blocked for classification={data_classification}",
                model_routing=routing_dict,
            )

        # ── Step 2: Live or mock call ─────────────────────────────────
        if not LLM_LIVE:
            result = self._mock_response(agent_route, input_text)
        else:
            result = self._live_call(agent_route, input_text, routing)

        # ── Step 3: Enrich with routing metadata ──────────────────────
        result.model_routing = routing_dict

        # ── Step 4: Audit ─────────────────────────────────────────────
        self._write_audit(agent_route, result, data_classification, traceability_id)

        return result

    def _mock_response(self, agent_route: str, input_text: str) -> LLMCallResult:
        """Return deterministic fixture responses per agent route."""
        if agent_route == "requirement_extractor":
            from .agents.requirement_extractor import requirement_fixture
            return LLMCallResult(json=requirement_fixture(), valid=True, attempt_count=1)
        if agent_route == "spec_composer":
            from .agents.spec_composer import specification_fixture
            return LLMCallResult(json=specification_fixture(), valid=True, attempt_count=1)
        return LLMCallResult(
            valid=False,
            reason_code="UNKNOWN_AGENT_ROUTE",
            detail=f"no mock response for agent_route={agent_route!r}",
        )

    def _live_call(self, agent_route: str, input_text: str, routing: ModelRouteDecision) -> LLMCallResult:
        """Make a real HTTP LLM call with retry + schema validation.

        Live mode requires CAD_AGENT_LLM_ENDPOINT and CAD_AGENT_LLM_API_KEY env vars.
        """
        endpoint = os.environ.get("CAD_AGENT_LLM_ENDPOINT")
        api_key = os.environ.get("CAD_AGENT_LLM_API_KEY")

        if not endpoint:
            return LLMCallResult(
                valid=False,
                reason_code="LLM_ENDPOINT_NOT_CONFIGURED",
                detail="CAD_AGENT_LLM_ENDPOINT env var not set",
            )

        system_prompt = self._system_prompt(agent_route)
        payload = {
            "model": os.environ.get("CAD_AGENT_LLM_MODEL", DEFAULT_MODEL),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ],
            "temperature": DEFAULT_TEMPERATURE,
        }

        import urllib.request
        import urllib.error

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        last_error: str | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
                last_error = str(exc)
                continue

            # Extract JSON from response
            content = self._extract_content(body)
            if content is None:
                last_error = "LLM response missing content"
                continue

            parsed = self._parse_json(content)
            if parsed is None:
                last_error = f"LLM response not valid JSON: {content[:200]}"
                continue

            if not self._validate_output(agent_route, parsed):
                last_error = f"schema validation failed for {agent_route}"
                continue

            return LLMCallResult(json=parsed, valid=True, attempt_count=attempt)

        return LLMCallResult(
            valid=False,
            reason_code="LLM_CALL_FAILED",
            detail=last_error or "all LLM attempts exhausted",
            attempt_count=MAX_RETRIES,
        )

    def _extract_content(self, response_body: dict[str, Any]) -> str | None:
        """Extract text content from an OpenAI-compatible response."""
        choices = response_body.get("choices", [])
        if not choices:
            return None
        message = choices[0].get("message", {})
        content = message.get("content")
        return content if isinstance(content, str) and content else None

    def _parse_json(self, text: str) -> dict[str, Any] | None:
        """Extract and parse JSON from LLM text output."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:]) if len(lines) > 1 else ""
            if text.endswith("```"):
                text = text[:-3]
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _validate_output(self, agent_route: str, output: dict[str, Any]) -> bool:
        """Validate LLM output against the appropriate schema."""
        from .platform_poc import validate_requirement_schema, validate_specification_schema, contract_status

        if agent_route == "requirement_extractor":
            checks = validate_requirement_schema(output)
        elif agent_route == "spec_composer":
            checks = validate_specification_schema(output)
        else:
            return False
        return contract_status(checks) == "pass"

    def _system_prompt(self, agent_route: str) -> str:
        if agent_route == "requirement_extractor":
            return (
                "You are a mechanical design requirement extractor. "
                "Given a natural language design description, output a JSON object with keys: "
                "traceability_id, product_type, functional_requirements (list), dimensions (object), "
                "manufacturing (object), unknowns (list), assumptions (list). "
                "Do not invent values for unknowns — list them explicitly. "
                "Output ONLY valid JSON, no markdown, no explanation."
            )
        if agent_route == "spec_composer":
            return (
                "You are a mechanical design specification composer. "
                "Given a requirement JSON, output a specification JSON with keys: "
                "traceability_id, requirement_id, parameter_table, constraints (list), "
                "material_candidates (list), manufacturing_profile, validation_plan (list), "
                "unresolved_risks (list). Use millimetres. Do not finalize tolerances — list them as proposals. "
                "Output ONLY valid JSON, no markdown, no explanation."
            )
        return "Output ONLY valid JSON."

    def _write_audit(
        self, agent_route: str, result: LLMCallResult, data_classification: str, traceability_id: str
    ) -> None:
        if self._audit_path is None:
            return
        event = {
            "event_id": f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "event_type": "llm_adapter_call",
            "agent_route": agent_route,
            "data_classification": data_classification,
            "model_routing": result.model_routing,
            "valid": result.valid,
            "reason_code": result.reason_code,
            "detail": result.detail,
            "attempt_count": result.attempt_count,
            "traceability_id": traceability_id,
            "live_mode": LLM_LIVE,
        }
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self._audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

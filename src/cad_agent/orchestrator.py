from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

CREATED = "created"
SPEC_PENDING_APPROVAL = "spec_pending_approval"
SPEC_APPROVED = "spec_approved"
DSL_GENERATED = "dsl_generated"
CAD_BUILT = "cad_built"
VALIDATION_RUNNING = "validation_running"
VALIDATION_PASSED = "validation_passed"
VALIDATION_FAILED = "validation_failed"
REVISION_REQUESTED = "revision_requested"
EXPORT_PENDING_APPROVAL = "export_pending_approval"
EXPORTED = "exported"
ESCALATED_TO_HUMAN = "escalated_to_human"

STATES = frozenset(
    {
        CREATED,
        SPEC_PENDING_APPROVAL,
        SPEC_APPROVED,
        DSL_GENERATED,
        CAD_BUILT,
        VALIDATION_RUNNING,
        VALIDATION_PASSED,
        VALIDATION_FAILED,
        REVISION_REQUESTED,
        EXPORT_PENDING_APPROVAL,
        EXPORTED,
        ESCALATED_TO_HUMAN,
    }
)

TRANSITIONS: dict[str, frozenset[str]] = {
    CREATED: frozenset({SPEC_PENDING_APPROVAL, SPEC_APPROVED, VALIDATION_FAILED, ESCALATED_TO_HUMAN}),
    SPEC_PENDING_APPROVAL: frozenset({SPEC_APPROVED, REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    SPEC_APPROVED: frozenset({DSL_GENERATED, CAD_BUILT, VALIDATION_FAILED, REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    DSL_GENERATED: frozenset({CAD_BUILT, REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    CAD_BUILT: frozenset({VALIDATION_RUNNING, REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    VALIDATION_RUNNING: frozenset({VALIDATION_PASSED, VALIDATION_FAILED, REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    VALIDATION_FAILED: frozenset({REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    REVISION_REQUESTED: frozenset({SPEC_PENDING_APPROVAL, DSL_GENERATED, VALIDATION_FAILED, ESCALATED_TO_HUMAN}),
    VALIDATION_PASSED: frozenset({EXPORT_PENDING_APPROVAL, REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    EXPORT_PENDING_APPROVAL: frozenset({EXPORTED, REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    EXPORTED: frozenset({REVISION_REQUESTED, ESCALATED_TO_HUMAN}),
    ESCALATED_TO_HUMAN: frozenset(),
}


@dataclass(frozen=True, slots=True)
class WorkflowDecision:
    blocked: bool = False
    approved: bool = False
    reason: str | None = None
    approval_id: str | None = None
    revision_request: "RevisionRequest | None" = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RevisionRequest:
    reason_codes: list[str]
    failure_locations: list[str] = field(default_factory=list)
    revision_count: int = 0
    payload: dict[str, Any] = field(default_factory=dict)


def audit_event(event_type: str, **payload: object) -> dict[str, Any]:
    return {"type": event_type, "traceability_id": payload.get("traceability_id"), "payload": _json_ready(payload)}


class Workflow:
    def __init__(self, state: str = CREATED, max_revision_loops: int = 3) -> None:
        if state not in STATES:
            raise ValueError(f"unknown workflow state: {state}")
        self._state = state
        self.max_revision_loops = max_revision_loops
        self.failure_count = 0
        self.events: list[dict[str, Any]] = []
        self.approval_decisions: list[dict[str, Any]] = []
        self.revision_requests: list[dict[str, Any]] = []

    @property
    def state(self) -> str:
        return self._state

    def approve_specification(self, specification_id: str, **payload: object) -> WorkflowDecision:
        approval = {
            "approval_type": "specification",
            "approved": True,
            "decision": "approved",
            "specification_id": specification_id,
            **_json_ready(payload),
        }
        self._transition(SPEC_APPROVED)
        event = self._record_event("specification_approved", traceability_id=specification_id, decision=approval, **payload)
        self.approval_decisions.append(approval)
        return WorkflowDecision(approved=True, approval_id=event["traceability_id"], payload=approval)

    def generate_dsl(self, traceability_id: str | None = None, **payload: object) -> WorkflowDecision:
        self._transition(DSL_GENERATED)
        event = self._record_event("dsl_generated", traceability_id=traceability_id, **payload)
        return WorkflowDecision(approved=True, approval_id=event["traceability_id"], payload=event["payload"])

    def run_cad(self, dsl: dict[str, Any], traceability_id: str | None = None, **payload: object) -> WorkflowDecision:
        if self._state != SPEC_APPROVED:
            return WorkflowDecision(blocked=True, reason="SPEC_APPROVAL_REQUIRED", payload={"dsl": _json_ready(dsl), **_json_ready(payload)})
        self._transition(CAD_BUILT)
        event = self._record_event("cad_built", traceability_id=traceability_id or dsl.get("traceability_id"), dsl=_json_ready(dsl), **payload)
        return WorkflowDecision(approved=True, approval_id=event["traceability_id"], payload=event["payload"])

    def start_validation(self, traceability_id: str | None = None, **payload: object) -> WorkflowDecision:
        self._transition(VALIDATION_RUNNING)
        event = self._record_event("validation_started", traceability_id=traceability_id, **payload)
        return WorkflowDecision(approved=True, approval_id=event["traceability_id"], payload=event["payload"])

    def handle_validation(self, validation_result: dict[str, Any], traceability_id: str | None = None, **payload: object) -> WorkflowDecision:
        normalized = _json_ready(validation_result)
        passed = bool(normalized.get("passed", normalized.get("pass", False)))
        reason_codes = _reason_codes(normalized)
        failure_locations = _failure_locations(normalized)
        resolved_traceability_id = traceability_id or normalized.get("traceability_id") or normalized.get("specification_id")

        if passed:
            self.failure_count = 0
            self._transition(VALIDATION_PASSED)
            event = self._record_event("validation_passed", traceability_id=resolved_traceability_id, result=normalized, **payload)
            return WorkflowDecision(approved=True, approval_id=event["traceability_id"], payload=event["payload"])

        self._transition(VALIDATION_FAILED)
        self._record_event("validation_failed", traceability_id=resolved_traceability_id, result=normalized, **payload)
        self.failure_count += 1

        revision_request = self.request_revision(
            reason_codes=reason_codes,
            failure_locations=failure_locations,
            traceability_id=resolved_traceability_id,
            validation_result=normalized,
            **payload,
        )

        if self.failure_count >= self.max_revision_loops:
            self._transition(ESCALATED_TO_HUMAN)
            escalation = self._record_event(
                "validation_escalated_to_human",
                traceability_id=resolved_traceability_id,
                reason="MAX_REVISION_LOOPS_REACHED",
                revision_request=asdict(revision_request),
                **payload,
            )
            return WorkflowDecision(blocked=True, reason="MAX_REVISION_LOOPS_REACHED", revision_request=revision_request, approval_id=escalation["traceability_id"])

        return WorkflowDecision(blocked=True, reason="VALIDATION_FAILED", revision_request=revision_request)

    def request_revision(self, reason_codes: list[str], failure_locations: list[str] | None = None, traceability_id: str | None = None, **payload: object) -> RevisionRequest:
        request = {
            "reason_codes": list(reason_codes),
            "failure_locations": list(failure_locations or []),
            "revision_count": self.failure_count,
            **_json_ready(payload),
        }
        self.revision_requests.append(request)
        self._transition(REVISION_REQUESTED)
        self._record_event("revision_requested", traceability_id=traceability_id, request=request, **payload)
        return RevisionRequest(
            reason_codes=request["reason_codes"],
            failure_locations=request["failure_locations"],
            revision_count=request["revision_count"],
            payload={key: value for key, value in request.items() if key not in {"reason_codes", "failure_locations", "revision_count"}},
        )

    def mark_validation_passed(self, traceability_id: str | None = None, **payload: object) -> WorkflowDecision:
        self._transition(VALIDATION_PASSED)
        event = self._record_event("validation_passed", traceability_id=traceability_id, **payload)
        return WorkflowDecision(approved=True, approval_id=event["traceability_id"], payload=event["payload"])

    def request_export(self, traceability_id: str | None = None, **payload: object) -> WorkflowDecision:
        if self._state != VALIDATION_PASSED:
            return WorkflowDecision(blocked=True, reason="VALIDATION_NOT_PASSED")
        self._transition(EXPORT_PENDING_APPROVAL)
        event = self._record_event("export_requested", traceability_id=traceability_id, **payload)
        return WorkflowDecision(blocked=True, reason="EXPORT_APPROVAL_REQUIRED", approval_id=event["traceability_id"], payload=event["payload"])

    def approve_export(self, export_id: str | None = None, **payload: object) -> WorkflowDecision:
        approval = {
            "approval_type": "export",
            "approved": True,
            "decision": "approved",
            "export_id": export_id,
            **_json_ready(payload),
        }
        self._transition(EXPORTED)
        event = self._record_event("export_approved", traceability_id=export_id, decision=approval, **payload)
        self.approval_decisions.append(approval)
        return WorkflowDecision(approved=True, approval_id=event["traceability_id"], payload=approval)

    def escalate_to_human(self, reason: str, traceability_id: str | None = None, **payload: object) -> WorkflowDecision:
        self._transition(ESCALATED_TO_HUMAN)
        event = self._record_event("escalated_to_human", traceability_id=traceability_id, reason=reason, **payload)
        return WorkflowDecision(blocked=True, reason=reason, approval_id=event["traceability_id"])

    def _transition(self, next_state: str) -> None:
        if not self._can_transition(next_state):
            raise ValueError(f"invalid workflow transition: {self._state} -> {next_state}")
        self._state = next_state

    def _can_transition(self, next_state: str) -> bool:
        return next_state in TRANSITIONS.get(self._state, frozenset())

    def _record_event(self, event_type: str, traceability_id: str | None = None, **payload: object) -> dict[str, Any]:
        event_payload = {"state": self._state, **_json_ready(payload)}
        if traceability_id is not None:
            event_payload.setdefault("traceability_id", traceability_id)
        event = audit_event(event_type, **event_payload)
        self.events.append(event)
        return event


def _reason_codes(validation_result: dict[str, Any]) -> list[str]:
    reason_codes = validation_result.get("reason_codes")
    if isinstance(reason_codes, list):
        return [str(reason_code) for reason_code in reason_codes]

    failures = validation_result.get("failures")
    if isinstance(failures, list):
        codes: list[str] = []
        for failure in failures:
            if isinstance(failure, dict):
                reason_code = failure.get("reason_code") or failure.get("code") or failure.get("status")
                if reason_code is not None:
                    codes.append(str(reason_code))
            elif failure is not None:
                codes.append(str(failure))
        return codes or ["VALIDATION_FAILED"]

    return ["VALIDATION_FAILED"]


def _failure_locations(validation_result: dict[str, Any]) -> list[str]:
    locations = validation_result.get("failure_locations")
    if isinstance(locations, list):
        return [str(location) for location in locations]

    failures = validation_result.get("failures")
    if isinstance(failures, list):
        found: list[str] = []
        for failure in failures:
            if isinstance(failure, dict):
                location = failure.get("failure_location") or failure.get("location")
                if location is not None:
                    found.append(str(location))
        return found

    return []


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_ready(item) for item in value]
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


__all__ = [
    "CAD_BUILT",
    "CREATED",
    "DSL_GENERATED",
    "ESCALATED_TO_HUMAN",
    "EXPORTED",
    "EXPORT_PENDING_APPROVAL",
    "REVISION_REQUESTED",
    "SPEC_APPROVED",
    "SPEC_PENDING_APPROVAL",
    "VALIDATION_FAILED",
    "VALIDATION_PASSED",
    "VALIDATION_RUNNING",
    "STATES",
    "TRANSITIONS",
    "Workflow",
    "WorkflowDecision",
    "RevisionRequest",
    "audit_event",
]

import json

from cad_agent.agents.common import retry_schema
from cad_agent.agents.mechanism_planner import plan_mechanism
from cad_agent.agents.requirement_extractor import extract_requirement, requirement_fixture
from cad_agent.agents.spec_composer import compose_specification
from cad_agent.platform_poc import validate_requirement_schema, validate_specification_schema


def test_agent_route_audit_records_route(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"

    result = extract_requirement(
        "Design a confidential fixture.",
        audit_path=audit_path,
        data_classification="confidential",
        model_route="commercial",
    )

    event = json.loads(audit_path.read_text().splitlines()[0])

    assert result.valid is True
    assert event["event_type"] == "agent_route_decision"
    assert event["route"] == "requirement_extractor"
    assert event["data_classification"] == "confidential"
    assert event["model_route"] == "commercial"
    assert event["retry_count"] == 0
    assert event["schema_status"] == "pass"
    assert event["model_routing"]["requires_approval"] is True


def test_requirement_extractor_route_metadata_includes_model_routing_decision() -> None:
    result = extract_requirement("Design a confidential fixture.", data_classification="confidential", model_route="commercial")

    assert result.valid is True
    assert result.metadata["model_routing"]["allowed"] is False
    assert result.metadata["model_routing"]["requires_approval"] is True


def test_requirement_extractor_returns_schema_valid_json() -> None:
    result = extract_requirement("Design a small kinetic object.")

    assert result.valid is True
    assert result.reason_code is None
    assert "unknowns" in result.json
    assert "assumptions" in result.json
    assert result.metadata["route"] == "requirement_extractor"
    assert result.metadata["deterministic"] is True

    checks = validate_requirement_schema(result.json)
    assert all(check.status == "pass" for check in checks), checks


def test_requirement_extractor_rejects_empty_input() -> None:
    result = extract_requirement("")

    assert result.valid is False
    assert result.reason_code == "INVALID_AGENT_INPUT"
    assert result.json == {}


def test_spec_composer_returns_schema_valid_json() -> None:
    result = compose_specification()

    assert result.valid is True
    assert result.reason_code is None
    assert result.metadata["route"] == "spec_composer"
    assert result.metadata["deterministic"] is True

    checks = validate_specification_schema(result.json)
    assert all(check.status == "pass" for check in checks), checks


def test_requirement_extractor_schema_retry_accepts_valid_attempt() -> None:
    result = extract_requirement(attempts=["invalid", requirement_fixture()], max_retries=2)

    assert result.valid is True
    assert result.reason_code is None
    assert result.metadata["route"] == "schema_retry"
    assert all(check.status == "pass" for check in validate_requirement_schema(result.json))


def test_retry_schema_accepts_valid_second_attempt() -> None:
    result = retry_schema(["invalid", '{"valid": true}'], max_retries=2)

    assert result.valid is True
    assert result.reason_code is None
    assert result.json == {"valid": True}
    assert result.metadata["attempt_count"] == 2


def test_retry_schema_records_invalid_attempt() -> None:
    result = retry_schema(["{not-json"], max_retries=1)

    assert result.valid is False
    assert result.reason_code == "SCHEMA_RETRY_EXHAUSTED"
    assert result.metadata["attempt_count"] == 1
    assert result.metadata["max_retries"] == 1


def test_retry_schema_max_retry_failure_is_structured() -> None:
    result = retry_schema(["invalid", "invalid"], max_retries=2)

    assert result.valid is False
    assert result.reason_code == "SCHEMA_RETRY_EXHAUSTED"
    assert result.metadata["route"] == "schema_retry"
    assert result.metadata["max_retries"] == 2


def test_mechanism_planner_returns_deterministic_plan() -> None:
    result = plan_mechanism()

    assert result.valid is True
    assert result.reason_code is None
    assert result.metadata["route"] == "mechanism_planner"
    assert result.metadata["deterministic"] is True
    assert result.json["traceability_id"] == "tr_mech_agent_fixture"
    assert result.json["operations"] == [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}]


# CAD-FG-04: Agent route hardening tests


def test_agent_routes_are_local_mock_fixtures() -> None:
    """CAD-FG-04: All agent routes must be local/mock fixtures, not real LLM endpoints."""
    result = extract_requirement("Design a test object.")
    assert result.metadata["deterministic"] is True
    assert result.metadata["model"] == "local_fixture"

    result2 = compose_specification()
    assert result2.metadata["deterministic"] is True
    assert result2.metadata["model"] == "local_fixture"

    result3 = plan_mechanism()
    assert result3.metadata["deterministic"] is True
    assert result3.metadata["model"] == "local_fixture"


def test_schema_retry_provides_structured_failure_evidence() -> None:
    """CAD-FG-04: Schema retry must provide structured failure reason codes."""
    result = retry_schema(["not-json", "{also-invalid}"], max_retries=2)

    assert result.valid is False
    assert result.reason_code == "SCHEMA_RETRY_EXHAUSTED"
    assert "errors" in result.metadata
    assert len(result.metadata["errors"]) == 2
    assert result.metadata["attempt_count"] == 2
    assert result.metadata["max_retries"] == 2


def test_agent_route_audit_includes_all_required_fields(tmp_path) -> None:
    """CAD-FG-04: Agent route audit must include route, model routing, data classification, retry/schema status, traceability, retention, timestamps."""
    audit_path = tmp_path / "audit.jsonl"

    result = extract_requirement(
        "Design a test object.",
        audit_path=audit_path,
        data_classification="internal",
        model_route="commercial",
    )

    event = json.loads(audit_path.read_text().splitlines()[0])

    # Required fields per CAD-FG-04
    assert "event_id" in event
    assert "recorded_at" in event
    assert "event_type" in event
    assert "route" in event
    assert "data_classification" in event
    assert "model_route" in event
    assert "model_routing" in event
    assert "retry_count" in event
    assert "schema_status" in event
    assert "traceability_id" in event
    assert "retention_days" in event


def test_model_routing_enforces_classification_policy() -> None:
    """CAD-FG-04: Model routing must enforce data classification policy."""
    # Confidential data should not use commercial route without approval
    result = extract_requirement(
        "Design a confidential object.",
        data_classification="confidential",
        model_route="commercial",
    )

    assert result.metadata["model_routing"]["allowed"] is False
    assert result.metadata["model_routing"]["requires_approval"] is True

    # Public data should be allowed on commercial route
    result2 = extract_requirement(
        "Design a public object.",
        data_classification="public",
        model_route="commercial",
    )

    assert result2.metadata["model_routing"]["allowed"] is True

from cad_agent.agents.common import retry_schema
from cad_agent.agents.mechanism_planner import plan_mechanism
from cad_agent.agents.requirement_extractor import extract_requirement, requirement_fixture
from cad_agent.agents.spec_composer import compose_specification
from cad_agent.platform_poc import validate_requirement_schema, validate_specification_schema


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

from cad_agent.agents.mechanism_planner import plan_mechanism
from cad_agent.agents.requirement_extractor import extract_requirement
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


def test_mechanism_planner_returns_deterministic_plan() -> None:
    result = plan_mechanism()

    assert result.valid is True
    assert result.reason_code is None
    assert result.metadata["route"] == "mechanism_planner"
    assert result.metadata["deterministic"] is True
    assert result.json["traceability_id"] == "tr_mech_agent_fixture"
    assert result.json["operations"] == [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}]

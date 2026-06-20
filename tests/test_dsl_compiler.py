from dataclasses import dataclass

from cad_agent.dsl_compiler import NEW_OPERATION_APPROVAL_REQUIRED, compile_mechanism_plan
from cad_agent.platform_poc import validate_parametric_dsl_ast
from cad_agent.schema_gate import ContractResult


@dataclass(frozen=True)
class Phase1Validation:
    passed: bool
    checks: tuple[ContractResult, ...]


def validate_phase1_dsl(dsl: dict[str, object]) -> Phase1Validation:
    checks = tuple(validate_parametric_dsl_ast(dsl))
    return Phase1Validation(passed=all(check.status == "pass" for check in checks), checks=checks)


def assert_parametric_dsl_ast_passes(dsl: dict[str, object]) -> None:
    checks = validate_parametric_dsl_ast(dsl)
    assert all(check.status == "pass" for check in checks), checks


def test_compiler_rejects_unsupported_operation() -> None:
    plan = {"operations": [{"op": "gear_raw_code", "code": "print('bad')"}]}

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == "UNSUPPORTED_MECHANISM_OP"
    assert result.dsl == {}


def test_compiler_emits_parametric_dsl_for_approved_shaft() -> None:
    plan = {
        "traceability_id": "tr_dsl_shaft_1",
        "operations": [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}],
    }

    result = compile_mechanism_plan(plan)

    assert result.valid is True
    assert result.reason_code is None
    assert "compiler" not in result.dsl
    assert result.dsl["units"] == "mm"
    assert result.dsl["traceability_id"] == "tr_dsl_shaft_1"
    assert result.dsl["parameters"] == {"radius": 5.0, "length": 50.0}
    assert result.dsl["features"] == [
        {
            "op": "cylinder",
            "radius_mm": "$radius",
            "height_mm": "$length",
            "axis": "z",
            "positions_mm": [[0, 0]],
        }
    ]
    assert result.dsl["derivative_outputs"] == ["step_ap242"]
    assert_parametric_dsl_ast_passes(result.dsl)


def test_compiler_emits_schema_valid_traceability_id_for_invalid_plan_id() -> None:
    plan = {
        "traceability_id": "tr-mech-1",
        "operations": [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}],
    }

    result = compile_mechanism_plan(plan)

    assert result.valid is True
    assert result.dsl["traceability_id"].startswith("tr_dsl_shaft_")
    assert result.dsl["traceability_id"] != "tr-mech-1"
    assert_parametric_dsl_ast_passes(result.dsl)


def test_compiler_output_passes_phase1_validation() -> None:
    plan = {"traceability_id": "tr-mech-2", "operations": [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}]}

    dsl = compile_mechanism_plan(plan).dsl
    validation = validate_phase1_dsl(dsl)

    assert validation.passed is True
    assert dsl["traceability_id"].startswith("tr_dsl_shaft_")


def test_compiler_rejects_unapproved_mechanism_operation() -> None:
    plan = {"operations": [{"op": "bearing_seat", "diameter_mm": 10, "length_mm": 50}]}

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == NEW_OPERATION_APPROVAL_REQUIRED
    assert result.dsl == {}


def test_compiler_new_operation_requires_approval() -> None:
    plan = {"operations": [{"op": "custom_gear"}]}

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == NEW_OPERATION_APPROVAL_REQUIRED
    assert result.dsl == {}


def test_compiler_rejects_unresolved_parameter_reference() -> None:
    plan = {"operations": [{"op": "shaft", "diameter_mm": "$missing", "length_mm": 50}]}

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == "INVALID_PARAMETER_REFERENCE"
    assert result.dsl == {}


def test_compiler_rejects_shaft_bad_positions() -> None:
    plan = {"traceability_id": "tr_dsl_shaft_1", "operations": [{"op": "shaft", "diameter_mm": 10, "length_mm": 50, "positions_mm": "bad"}]}

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == "INVALID_POSITIONS_MM"
    assert result.dsl == {}


def test_compiler_allows_only_current_phase1_dsl_operations() -> None:
    plan = {
        "traceability_id": "tr_dsl_allowlist",
        "operations": [
            {"op": "box", "length_mm": "$length", "width_mm": "$width", "height_mm": "$height"},
            {"op": "cylinder", "radius_mm": "$radius", "height_mm": "$height", "axis": "z", "positions_mm": [[0, 0]]},
            {"op": "through_hole", "diameter_mm": "$hole", "depth_mm": "$height", "axis": "z", "positions_mm": [[0, 0]]},
        ],
        "parameters": {"length": 20, "width": 10, "height": 5, "radius": 3, "hole": 2},
    }

    result = compile_mechanism_plan(plan)

    assert result.valid is True
    assert result.reason_code is None
    assert "compiler" not in result.dsl
    assert result.dsl["traceability_id"] == "tr_dsl_allowlist"
    assert result.dsl["units"] == "mm"
    assert_parametric_dsl_ast_passes(result.dsl)


def test_compiler_rejects_phase1_passthrough_unresolved_reference() -> None:
    plan = {
        "traceability_id": "tr_dsl_allowlist",
        "operations": [{"op": "box", "length_mm": "$missing", "width_mm": "$width", "height_mm": "$height"}],
        "parameters": {"width": 10, "height": 5},
    }

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == "INVALID_PARAMETER_REFERENCE"
    assert result.dsl == {}


def test_compiler_rejects_phase1_passthrough_bad_positions() -> None:
    plan = {
        "traceability_id": "tr_dsl_allowlist",
        "operations": [{"op": "cylinder", "radius_mm": "$radius", "height_mm": "$height", "axis": "z", "positions_mm": "bad"}],
        "parameters": {"radius": 3, "height": 5},
    }

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == "INVALID_POSITIONS_MM"
    assert result.dsl == {}

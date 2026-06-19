from cad_agent.dsl_compiler import ALLOWED_DSL_OPERATIONS, compile_mechanism_plan


def test_compiler_rejects_unsupported_operation() -> None:
    plan = {"operations": [{"op": "gear_raw_code", "code": "print('bad')"}]}

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == "UNSUPPORTED_MECHANISM_OP"
    assert result.dsl == {}


def test_compiler_emits_parametric_dsl_for_approved_shaft() -> None:
    plan = {
        "traceability_id": "tr-mech-1",
        "operations": [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}],
    }

    result = compile_mechanism_plan(plan)

    assert result.valid is True
    assert result.reason_code is None
    assert result.dsl["units"] == "mm"
    assert result.dsl["traceability_id"] == "tr-mech-1"
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
    assert result.dsl["compiler"]["mechanism_operations_accepted"] is True


def test_compiler_rejects_unapproved_mechanism_operation() -> None:
    plan = {"operations": [{"op": "bearing_seat", "diameter_mm": 10, "length_mm": 50}]}

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == "UNSUPPORTED_MECHANISM_OP"
    assert result.dsl == {}


def test_compiler_rejects_unresolved_parameter_reference() -> None:
    plan = {"operations": [{"op": "shaft", "diameter_mm": "$missing", "length_mm": 50}]}

    result = compile_mechanism_plan(plan)

    assert result.valid is False
    assert result.reason_code == "INVALID_PARAMETER_REFERENCE"
    assert result.dsl == {}


def test_compiler_allows_only_current_phase1_dsl_operations() -> None:
    plan = {
        "traceability_id": "tr_mech_allowlist",
        "operations": [
            {"op": "box", "length_mm": "$length", "width_mm": "$width", "height_mm": "$height"},
            {"op": "cylinder", "radius_mm": "$radius", "height_mm": "$height"},
            {"op": "through_hole", "diameter_mm": "$hole", "depth_mm": "$height"},
        ],
        "parameters": {"length": 20, "width": 10, "height": 5, "radius": 3, "hole": 2},
    }

    result = compile_mechanism_plan(plan)

    assert result.valid is True
    assert result.reason_code is None
    assert result.dsl["traceability_id"] == "tr_mech_allowlist"
    assert result.dsl["units"] == "mm"
    assert result.dsl["compiler"]["allowlist"] == sorted(ALLOWED_DSL_OPERATIONS)
    assert result.dsl["compiler"]["mechanism_operations_accepted"] is False

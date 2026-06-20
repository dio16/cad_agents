from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from cad_agent.orchestrator import VALIDATION_PASSED, Workflow


EXPORT_APPROVAL_REQUIRED = "EXPORT_APPROVAL_REQUIRED"
from cad_agent.platform_poc import (
    contract_status,
    run_cad_runtime,
    validate_artifacts,
    validate_parametric_dsl_ast,
    validate_parametric_dsl_schema,
    validate_requirement_schema,
    validate_specification_schema,
    validate_validation_report_schema,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "artifacts" / "gyro_kinetic_v1"
TARGET_SPEC_PATH = TARGET_DIR / "target_spec.json"
TARGET_REQUIREMENT_PATH = TARGET_DIR / "requirement.json"
TARGET_SPECIFICATION_PATH = TARGET_DIR / "specification.json"
TARGET_DSL_PATH = TARGET_DIR / "dsl.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_target_spec() -> dict:
    return _load_json(TARGET_SPEC_PATH)


def load_target_requirement() -> dict:
    return _load_json(TARGET_REQUIREMENT_PATH)


def load_target_specification() -> dict:
    return _load_json(TARGET_SPECIFICATION_PATH)


def load_target_dsl() -> dict:
    return _load_json(TARGET_DSL_PATH)


def build_review_package_fixture() -> dict:
    target_spec = load_target_spec()
    dsl = load_target_dsl()
    with TemporaryDirectory() as temp_dir:
        runtime = run_cad_runtime(dsl, Path(temp_dir) / "runtime")
        validation = validate_artifacts(load_target_specification(), dsl, runtime)
    return {
        "traceability_id": target_spec["traceability_id"],
        "target_name": target_spec["target_name"],
        "approval": target_spec["approval"],
        "traceability": {
            "requirement_id": load_target_requirement()["traceability_id"],
            "specification_id": load_target_specification()["traceability_id"],
            "dsl_id": dsl["traceability_id"],
            "validation_report_id": validation["traceability_id"],
        },
        "validation": {
            "pass": validation["pass"],
            "artifact_ids": validation["artifact_ids"],
        },
        "runtime": {
            "status": runtime["status"],
            "artifact_formats": [artifact["format"] for artifact in runtime["artifacts"]],
        },
    }


def test_target_spec_requires_approval() -> None:
    spec = load_target_spec()

    assert spec["traceability_id"].startswith("tr_target_")
    assert spec["target_name"] == "gyro_kinetic_v1"
    assert spec["approval"] == {
        "specification_freeze": True,
        "approved_by": "user",
        "approval_event": "artifacts/gyro_kinetic_v1/target_spec.json を承認",
        "recorded_at": "2026-06-20T00:00:00+00:00",
    }
    assert spec["approval"]["specification_freeze"] is True


def test_target_requirement_schema_valid() -> None:
    checks = validate_requirement_schema(load_target_requirement())

    assert contract_status(checks) == "pass"


def test_target_specification_schema_valid() -> None:
    checks = validate_specification_schema(load_target_specification())

    assert contract_status(checks) == "pass"


def test_target_dsl_passes_phase1_schema_and_ast_validation() -> None:
    dsl = load_target_dsl()

    assert dsl["units"] == "mm"
    assert {feature["op"] for feature in dsl["features"]} <= {"box", "through_hole"}
    assert all(feature.get("axis", "z") == "z" for feature in dsl["features"])
    assert dsl["derivative_outputs"] == ["step_ap242", "stl"]
    assert contract_status(validate_parametric_dsl_schema(dsl)) == "pass"
    assert contract_status(validate_parametric_dsl_ast(dsl)) == "pass"


def test_target_cad_run_generates_metadata_artifact() -> None:
    dsl = load_target_dsl()

    with TemporaryDirectory() as temp_dir:
        runtime = run_cad_runtime(dsl, Path(temp_dir) / "runtime")
        metadata_artifacts = [artifact for artifact in runtime["artifacts"] if artifact["format"] == "metadata"]
        metadata_path = Path(metadata_artifacts[0]["path"]) if metadata_artifacts else Path()

        assert runtime["status"] == "pass"
        assert len(metadata_artifacts) == 1
        assert metadata_artifacts[0]["artifact_id"] == f"art_{dsl['traceability_id']}_metadata"
        assert metadata_path.exists()


def test_target_validation_report_passes() -> None:
    dsl = load_target_dsl()

    with TemporaryDirectory() as temp_dir:
        runtime = run_cad_runtime(dsl, Path(temp_dir) / "runtime")
        validation = validate_artifacts(load_target_specification(), dsl, runtime)

    assert runtime["status"] == "pass"
    assert validation["pass"] is True
    assert validation["traceability_id"].startswith("tr_val_")
    assert contract_status(validate_validation_report_schema(validation)) == "pass"
    for check_name in ["dimensions_check", "topology_check", "unit_consistency", "manufacturing_profile_rules"]:
        assert validation[check_name]["status"] == "pass"


def test_workflow_export_still_requires_approval_after_validation_pass() -> None:
    result = Workflow(VALIDATION_PASSED).request_export(load_target_dsl()["traceability_id"])

    assert result.blocked is True
    assert result.reason == EXPORT_APPROVAL_REQUIRED


def test_review_package_fixture_contains_traceability() -> None:
    package = build_review_package_fixture()

    assert package["traceability_id"] == load_target_spec()["traceability_id"]
    assert package["target_name"] == "gyro_kinetic_v1"
    assert package["approval"]["approval_event"] == "artifacts/gyro_kinetic_v1/target_spec.json を承認"
    assert package["traceability"]["requirement_id"].startswith("tr_req_")
    assert package["traceability"]["specification_id"].startswith("tr_spec_")
    assert package["traceability"]["dsl_id"].startswith("tr_dsl_")
    assert package["traceability"]["validation_report_id"].startswith("tr_val_")
    assert package["validation"]["pass"] is True
    assert "metadata" in package["runtime"]["artifact_formats"]

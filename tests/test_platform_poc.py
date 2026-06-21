from __future__ import annotations

import json
import subprocess
import sys
import types
import unittest
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from cad_agent.platform_poc import (
    contract_report,
    contract_status,
    golden_dsl,
    golden_requirement,
    golden_specification,
    record_human_approval,
    run_cad_runtime,
    run_golden_pipeline,
    store_artifacts,
    validate_artifacts,
    validate_parametric_dsl_ast,
    validate_parametric_dsl_schema,
    validate_requirement_schema,
    validate_specification_schema,
    validate_validation_report_schema,
)
import cad_agent.platform_poc as platform_poc
from cad_agent.schema_gate import validate_against_schema


ROOT = Path(__file__).resolve().parents[1]


class PlatformPocTest(unittest.TestCase):
    def test_contract_report_passes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = contract_report(Path(temp_dir) / "runtime")
        self.assertEqual(report["status"], "pass")

    def test_phase1_json_schema_files_are_present(self) -> None:
        schema_dir = files("cad_agent.contracts.phase1")
        expected = {
            "requirement.schema.json",
            "specification.schema.json",
            "parametric_dsl.schema.json",
            "validation_report.schema.json",
        }
        self.assertEqual({path.name for path in schema_dir.iterdir() if path.name.endswith(".schema.json")}, expected)
        for schema_path in schema_dir.iterdir():
            if not schema_path.name.endswith(".schema.json"):
                continue
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertIn("required", schema)
            self.assertEqual(schema["type"], "object")

    def test_golden_documents_pass_schema_gate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            requirement = golden_requirement()
            specification = golden_specification()
            dsl = golden_dsl()
            runtime = run_cad_runtime(dsl, tmp_path / "runtime")
            validation = validate_artifacts(specification, dsl, runtime)

        groups = {
            "requirement": validate_requirement_schema(requirement),
            "specification": validate_specification_schema(specification),
            "parametric_dsl": validate_parametric_dsl_schema(dsl),
            "validation_report": validate_validation_report_schema(validation),
        }
        self.assertTrue(all(contract_status(checks) == "pass" for checks in groups.values()))

    def test_validation_report_schema_rejects_weak_failure_item(self) -> None:
        validation = validate_artifacts(golden_specification(), golden_dsl(), {"status": "fail", "reason_code": "CAD_RUNTIME_FAILED", "artifacts": []})
        validation["dimensions_check"]["status"] = "unknown"
        validation["failures"] = [{"failure_location": "cad_runtime"}]

        checks = validate_validation_report_schema(validation)

        self.assertEqual(contract_status(checks), "fail")

    def test_validation_report_schema_rejects_failed_check_without_reason_code_or_detail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            validation = validate_artifacts(golden_specification(), golden_dsl(), run_cad_runtime(golden_dsl(), Path(temp_dir) / "unused"))
        validation["pass"] = False
        validation["dimensions_check"]["status"] = "fail"
        validation["dimensions_check"].pop("reason_code")
        validation["dimensions_check"].pop("detail")
        validation["failures"].append({"reason_code": "DIMENSION_FAILURE", "failure_location": "dimensions_check", "detail": "missing dimensions"})

        checks = validate_validation_report_schema(validation)

        self.assertEqual(contract_status(checks), "fail")

    def test_validation_report_schema_rejects_pass_fail_inconsistency(self) -> None:
        with TemporaryDirectory() as temp_dir:
            validation = validate_artifacts(golden_specification(), golden_dsl(), run_cad_runtime(golden_dsl(), Path(temp_dir) / "unused"))
        validation["pass"] = False

        checks = validate_validation_report_schema(validation)

        self.assertEqual(contract_status(checks), "fail")

    def test_failed_validation_report_contains_revision_feedback(self) -> None:
        validation = validate_artifacts(
            golden_specification(),
            golden_dsl(),
            {"status": "fail", "reason_code": "CAD_RUNTIME_FAILED", "artifacts": []},
        )

        self.assertFalse(validation["pass"])
        self.assertIsInstance(validation["revision_feedback"], list)
        self.assertTrue(validation["revision_feedback"])
        self.assertTrue(
            all(
                {"reason_code", "failed_checks", "suggested_revision_action", "traceability_link"} <= set(feedback)
                for feedback in validation["revision_feedback"]
            )
        )
        self.assertTrue(any(feedback["reason_code"] == "CAD_RUNTIME_FAILED" for feedback in validation["revision_feedback"]))

    def test_passing_validation_report_has_empty_revision_feedback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            validation = validate_artifacts(golden_specification(), golden_dsl(), run_cad_runtime(golden_dsl(), Path(temp_dir) / "unused"))

        self.assertTrue(validation["pass"])
        self.assertEqual(validation["revision_feedback"], [])

    def test_validation_report_schema_rejects_failed_report_without_revision_feedback(self) -> None:
        validation = validate_artifacts(
            golden_specification(),
            golden_dsl(),
            {"status": "fail", "reason_code": "CAD_RUNTIME_FAILED", "artifacts": []},
        )
        validation.pop("revision_feedback")

        checks = validate_validation_report_schema(validation)

        self.assertEqual(contract_status(checks), "fail")
        self.assertIn("revision_feedback", checks[0].detail)

    def test_schema_gate_rejects_unknown_schema_name(self) -> None:
        checks = validate_against_schema(golden_requirement(), "unknown_schema")

        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].status, "fail")
        self.assertIn("unknown Phase 1 schema name", checks[0].detail)

    def test_schema_gate_rejects_invalid_requirement(self) -> None:
        requirement = golden_requirement()
        del requirement["traceability_id"]

        checks = validate_requirement_schema(requirement)

        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].status, "fail")
        self.assertIn("traceability_id", checks[0].detail)

    def test_schema_gate_rejects_unknown_root_property(self) -> None:
        requirement = golden_requirement()
        requirement["unexpected"] = "not allowed"

        checks = validate_requirement_schema(requirement)

        self.assertEqual(contract_status(checks), "fail")
        self.assertIn("Additional properties", checks[0].detail)

    def test_schema_gate_rejects_invalid_traceability_pattern(self) -> None:
        requirement = golden_requirement()
        requirement["traceability_id"] = "bad-id"

        checks = validate_requirement_schema(requirement)

        self.assertEqual(contract_status(checks), "fail")
        self.assertIn("does not match", checks[0].detail)

    def test_parametric_dsl_schema_rejects_missing_nested_feature_fields(self) -> None:
        dsl = golden_dsl()
        del dsl["features"][1]["positions_mm"]

        checks = validate_parametric_dsl_schema(dsl)

        self.assertEqual(contract_status(checks), "fail")
        self.assertIn("positions_mm", checks[0].detail)

    def test_parametric_dsl_schema_rejects_non_reference_dimension_string(self) -> None:
        dsl = golden_dsl()
        dsl["features"][0]["length_mm"] = "abc"

        checks = validate_parametric_dsl_schema(dsl)

        self.assertEqual(contract_status(checks), "fail")
        self.assertIn("abc", checks[0].detail)

    def test_ast_validator_rejects_non_reference_dimension_string(self) -> None:
        dsl = golden_dsl()
        dsl["features"][0]["length_mm"] = "abc"

        checks = validate_parametric_dsl_ast(dsl)

        self.assertEqual(contract_status(checks), "fail")
        ref_check = next(check for check in checks if check.name == "Parametric DSL parameter references resolve")
        self.assertEqual(ref_check.status, "fail")
        self.assertIn("abc", ref_check.detail)

    def test_parametric_dsl_schema_rejects_axis_other_than_z(self) -> None:
        dsl = golden_dsl()
        dsl["features"][1]["axis"] = "x"

        checks = validate_parametric_dsl_schema(dsl)

        self.assertEqual(contract_status(checks), "fail")
        self.assertIn("axis", checks[0].detail)

    def test_ast_validator_rejects_axis_other_than_z(self) -> None:
        dsl = golden_dsl()
        dsl["features"][1]["axis"] = "x"

        checks = validate_parametric_dsl_ast(dsl)

        self.assertEqual(contract_status(checks), "fail")
        axis_check = next(check for check in checks if check.name == "Parametric DSL axis support is z-only")
        self.assertEqual(axis_check.status, "fail")
        self.assertIn("axis=x", axis_check.detail)

    def test_parametric_dsl_schema_requires_step_ap242_output(self) -> None:
        dsl = golden_dsl()
        dsl["derivative_outputs"] = ["stl"]

        checks = validate_parametric_dsl_schema(dsl)

        self.assertEqual(contract_status(checks), "fail")
        self.assertIn("does not contain", checks[0].detail)

    def test_runtime_returns_export_failed_for_cadquery_export_error(self) -> None:
        exporter = types.ModuleType("cadquery")
        exporters = types.ModuleType("cadquery.exporters")

        def fail_export(*args: object, **kwargs: object) -> None:
            raise RuntimeError("export unavailable")

        setattr(exporters, "export", fail_export)
        setattr(exporter, "exporters", exporters)

        dsl = golden_dsl()
        with TemporaryDirectory() as temp_dir:
            with (
                patch.object(platform_poc, "_cadquery_available", return_value=True),
                patch.object(platform_poc, "_build_cadquery_model", return_value=object()),
                patch.object(platform_poc, "_model_bbox_mm", return_value=(64.0, 32.0, 8.0)),
                patch.object(platform_poc, "_model_volume_mm3", return_value=16384.0),
                patch.dict(sys.modules, {"cadquery": exporter}),
            ):
                result = platform_poc.run_cad_runtime(dsl, Path(temp_dir) / "runtime")

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["reason_code"], "EXPORT_FAILED")
        self.assertIn("STEP export failed", result["detail"])
        self.assertEqual(result["failed_export"], {"format": "step_ap242", "path": str(Path(temp_dir) / "runtime" / f"{dsl['traceability_id']}.step")})
        self.assertEqual(result["artifacts"], [])

    def test_ast_validator_rejects_unknown_parameter_reference(self) -> None:
        dsl = golden_dsl()
        dsl["features"][0]["length_mm"] = "$missing_length"
        checks = validate_parametric_dsl_ast(dsl)
        self.assertEqual(contract_status(checks), "fail")
        self.assertTrue(any(check.name == "Parametric DSL parameter references resolve" and check.status == "fail" for check in checks))

    def test_ast_validator_rejects_additive_op_after_subtractive_op(self) -> None:
        dsl = golden_dsl()
        dsl["features"].append({"op": "box", "length_mm": "$length", "width_mm": "$width", "height_mm": "$height"})

        checks = validate_parametric_dsl_ast(dsl)

        self.assertEqual(contract_status(checks), "fail")
        order_check = next(check for check in checks if check.name == "Parametric DSL feature order is executable")
        self.assertEqual(order_check.status, "fail")
        self.assertIn("additive op follows subtractive op", order_check.detail)

    def test_ast_validator_rejects_subtractive_op_without_additive_base(self) -> None:
        dsl = golden_dsl()
        dsl["features"] = [dsl["features"][1]]

        checks = validate_parametric_dsl_ast(dsl)

        self.assertEqual(contract_status(checks), "fail")
        order_check = next(check for check in checks if check.name == "Parametric DSL feature order is executable")
        self.assertEqual(order_check.status, "fail")
        self.assertIn("subtractive op precedes additive base", order_check.detail)

    def test_cli_status_and_phase1_contract_test(self) -> None:
        status = subprocess.run(
            [sys.executable, "-m", "cad_agent.cli", "status"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["status"], "aligned")

        contract_test = subprocess.run(
            [sys.executable, "-m", "cad_agent.cli", "phase1-contract-test"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(contract_test.returncode, 0, contract_test.stderr)
        self.assertEqual(json.loads(contract_test.stdout)["status"], "pass")

    def test_runtime_validation_and_artifact_store(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            dsl = golden_dsl()
            spec = golden_specification()
            runtime = run_cad_runtime(dsl, tmp_path / "runtime")
            validation = validate_artifacts(spec, dsl, runtime)
            store = store_artifacts(runtime, validation, tmp_path / "store")

            metadata_artifacts = [artifact for artifact in runtime["artifacts"] if artifact["format"] == "metadata"]
            self.assertEqual(len(metadata_artifacts), 1)
            metadata_path = Path(metadata_artifacts[0]["path"])
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertIn("cad_kernel", metadata)
            self.assertEqual(metadata_artifacts[0]["artifact_hash"], platform_poc.stable_hash_file(metadata_path))

            self.assertEqual(runtime["status"], "pass")
            self.assertTrue(validation["pass"])
            self.assertEqual(validation["revision_feedback"], [])
            self.assertEqual(validation["artifact_provenance_check"]["status"], "pass")
            self.assertEqual(store["status"], "pass")
            self.assertEqual({record["format"] for record in store["records"]}, {"step_ap242", "stl", "metadata", "validation_report"})
            self.assertTrue(all(record["traceability_id"] == dsl["traceability_id"] for record in store["records"]))
            self.assertTrue(all(record["artifact_hash"].startswith("sha256:") for record in store["records"]))

    def test_validation_report_requires_metadata_artifact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            runtime = run_cad_runtime(golden_dsl(), Path(temp_dir) / "runtime")
            runtime["artifacts"] = [artifact for artifact in runtime["artifacts"] if artifact["format"] != "metadata"]
            validation = validate_artifacts(golden_specification(), golden_dsl(), runtime)

        self.assertFalse(validation["pass"])
        self.assertEqual(validation["artifact_provenance_check"]["status"], "fail")
        self.assertTrue(any(failure["reason_code"] == "MISSING_METADATA_ARTIFACT" for failure in validation["failures"]))
        self.assertTrue(any(feedback["reason_code"] == "MISSING_METADATA_ARTIFACT" for feedback in validation["revision_feedback"]))

    def test_validation_report_requires_metadata_cad_kernel(self) -> None:
        with TemporaryDirectory() as temp_dir:
            runtime = run_cad_runtime(golden_dsl(), Path(temp_dir) / "runtime")
            metadata_artifact = next(artifact for artifact in runtime["artifacts"] if artifact["format"] == "metadata")
            metadata_path = Path(metadata_artifact["path"])
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            del metadata["cad_kernel"]
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

            validation = validate_artifacts(golden_specification(), golden_dsl(), runtime)

        self.assertFalse(validation["pass"])
        self.assertEqual(validation["artifact_provenance_check"]["status"], "fail")
        self.assertTrue(any(failure["reason_code"] == "METADATA_MISSING_CAD_KERNEL" for failure in validation["failures"]))
        self.assertTrue(any(feedback["reason_code"] == "METADATA_MISSING_CAD_KERNEL" for feedback in validation["revision_feedback"]))

    def test_validation_report_rejects_invalid_artifact_hash(self) -> None:
        with TemporaryDirectory() as temp_dir:
            runtime = run_cad_runtime(golden_dsl(), Path(temp_dir) / "runtime")
            runtime["artifacts"][0]["artifact_hash"] = "sha256:invalid"

            validation = validate_artifacts(golden_specification(), golden_dsl(), runtime)

        self.assertFalse(validation["pass"])
        self.assertEqual(validation["artifact_provenance_check"]["status"], "fail")
        self.assertTrue(any(failure["reason_code"] == "ARTIFACT_HASH_MISMATCH" for failure in validation["failures"]))
        self.assertTrue(any(feedback["reason_code"] == "ARTIFACT_HASH_MISMATCH" for feedback in validation["revision_feedback"]))

    def test_validation_report_handles_non_dict_artifact_entry(self) -> None:
        with TemporaryDirectory() as temp_dir:
            runtime = run_cad_runtime(golden_dsl(), Path(temp_dir) / "runtime")
            runtime["artifacts"].append("not-an-artifact")

            validation = validate_artifacts(golden_specification(), golden_dsl(), runtime)

        self.assertFalse(validation["pass"])
        self.assertEqual(validation["artifact_provenance_check"]["status"], "fail")
        self.assertTrue(any(failure["reason_code"] == "ARTIFACT_ENTRY_INVALID" for failure in validation["failures"]))
        self.assertTrue(any(feedback["reason_code"] == "ARTIFACT_ENTRY_INVALID" for feedback in validation["revision_feedback"]))

    def test_validation_report_reports_artifact_id_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            runtime = run_cad_runtime(golden_dsl(), Path(temp_dir) / "runtime")
            runtime["artifacts"].append({"path": str(Path(temp_dir) / "missing.step"), "artifact_hash": "sha256:invalid"})

            validation = validate_artifacts(golden_specification(), golden_dsl(), runtime)

        self.assertFalse(validation["pass"])
        self.assertEqual(validation["artifact_provenance_check"]["status"], "fail")
        self.assertTrue(any(failure["reason_code"] == "ARTIFACT_ID_MISSING" for failure in validation["failures"]))
        self.assertTrue(any(feedback["reason_code"] == "ARTIFACT_ID_MISSING" for feedback in validation["revision_feedback"]))

    def test_validation_report_reports_artifact_path_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            runtime = run_cad_runtime(golden_dsl(), Path(temp_dir) / "runtime")
            runtime["artifacts"].append({"artifact_id": f"art_{golden_dsl()['traceability_id']}_missing", "artifact_hash": "sha256:invalid"})

            validation = validate_artifacts(golden_specification(), golden_dsl(), runtime)

        self.assertFalse(validation["pass"])
        self.assertEqual(validation["artifact_provenance_check"]["status"], "fail")
        self.assertTrue(any(failure["reason_code"] == "ARTIFACT_PATH_MISSING" for failure in validation["failures"]))
        self.assertTrue(any(feedback["reason_code"] == "ARTIFACT_PATH_MISSING" for feedback in validation["revision_feedback"]))

    def test_human_approval_gate_records_override_decision(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = record_human_approval(
                traceability_id="tr_dsl_phase1_pipe_clamp",
                approval_type="validation_override",
                approver="reviewer_001",
                decision="rejected",
                reason="override not needed for passing validation",
                approval_dir=tmp_path,
            )
            approval_path = Path(result["approval_path"])
            rows = [json.loads(line) for line in approval_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[-1]["approval_type"], "validation_override")
            self.assertEqual(rows[-1]["decision"], "rejected")

    def test_human_approval_gate_records_required_escalations(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            for approval_type in ["regulated_tag", "export_controlled_tag", "new_dsl_operation"]:
                result = record_human_approval(
                    traceability_id="tr_dsl_phase1_pipe_clamp",
                    approval_type=approval_type,
                    approver="reviewer_001",
                    decision="rejected",
                    reason=f"{approval_type} requires human approval",
                    approval_dir=tmp_path,
                )
                self.assertEqual(result["status"], "pass")

            approval_path = Path(result["approval_path"])
            rows = [json.loads(line) for line in approval_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual({row["approval_type"] for row in rows[-3:]}, {"regulated_tag", "export_controlled_tag", "new_dsl_operation"})

    def test_human_approval_gate_rejects_unknown_type(self) -> None:
        with self.assertRaises(ValueError):
            record_human_approval(
                traceability_id="tr_dsl_phase1_pipe_clamp",
                approval_type="unknown",
                approver="reviewer_001",
                decision="approved",
                reason="not allowed",
                approval_dir=Path("unused"),
            )

    def test_golden_pipeline_passes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            report = run_golden_pipeline(tmp_path / "golden")
            self.assertEqual(report["status"], "pass")
            self.assertTrue((tmp_path / "golden" / "phase1_poc_report.json").exists())


if __name__ == "__main__":
    unittest.main()

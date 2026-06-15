from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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


ROOT = Path(__file__).resolve().parents[1]


class PlatformPocTest(unittest.TestCase):
    def test_contract_report_passes(self) -> None:
        report = contract_report()
        self.assertEqual(report["status"], "pass")

    def test_phase1_json_schema_files_are_present(self) -> None:
        schema_dir = Path("schemas/phase1")
        expected = {
            "requirement.schema.json",
            "specification.schema.json",
            "parametric_dsl.schema.json",
            "validation_report.schema.json",
        }
        self.assertEqual({path.name for path in schema_dir.glob("*.schema.json")}, expected)
        for schema_path in schema_dir.glob("*.schema.json"):
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

    def test_schema_gate_rejects_invalid_requirement(self) -> None:
        requirement = golden_requirement()
        del requirement["traceability_id"]

        checks = validate_requirement_schema(requirement)

        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].status, "fail")
        self.assertIn("traceability_id", checks[0].detail)

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
            [sys.executable, "-m", "cad_agent_cli", "status"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["status"], "aligned")

        contract_test = subprocess.run(
            [sys.executable, "-m", "cad_agent_cli", "phase1-contract-test"],
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

            self.assertEqual(runtime["status"], "pass")
            self.assertTrue(validation["pass"])
            self.assertEqual(store["status"], "pass")
            self.assertEqual({record["format"] for record in store["records"]}, {"step_ap242", "stl", "metadata", "validation_report"})
            self.assertTrue(all(record["traceability_id"] == dsl["traceability_id"] for record in store["records"]))
            self.assertTrue(all(record["artifact_hash"].startswith("sha256:") for record in store["records"]))

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

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cad_agent.platform_poc import (
    contract_report,
    contract_status,
    golden_dsl,
    golden_specification,
    record_human_approval,
    run_cad_runtime,
    run_golden_pipeline,
    store_artifacts,
    validate_artifacts,
    validate_parametric_dsl_ast,
)


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

    def test_ast_validator_rejects_unknown_parameter_reference(self) -> None:
        dsl = golden_dsl()
        dsl["features"][0]["length_mm"] = "$missing_length"
        checks = validate_parametric_dsl_ast(dsl)
        self.assertEqual(contract_status(checks), "fail")
        self.assertTrue(any(check.name == "Parametric DSL parameter references resolve" and check.status == "fail" for check in checks))

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

    def test_golden_pipeline_passes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            report = run_golden_pipeline(tmp_path / "golden")
            self.assertEqual(report["status"], "pass")
            self.assertTrue((tmp_path / "golden" / "phase1_poc_report.json").exists())


if __name__ == "__main__":
    unittest.main()

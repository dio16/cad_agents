"""Tests for E2E job runner — fixture_pipeline and structured_pipeline modes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from cad_agent.job_runner import ALLOWED_MODES, JobResult, run_job
from cad_agent.platform_poc import golden_dsl, golden_requirement, golden_specification

ROOT = Path(__file__).resolve().parents[1]


class JobRunnerTest(TestCase):
    def test_fixture_pipeline_produces_validation_passed(self) -> None:
        """fixture_pipeline must complete with validation_passed state."""
        with TemporaryDirectory() as tmp:
            result = run_job({"mode": "fixture_pipeline"}, output_dir=Path(tmp) / "out")
        self.assertFalse(result.blocked, f"blocked: reason={result.reason_code} detail={result.detail}")
        self.assertEqual(result.state, "validation_passed")
        self.assertIsNotNone(result.requirement)
        self.assertIsNotNone(result.specification)
        self.assertIsNotNone(result.dsl)
        self.assertIsNotNone(result.runtime)
        self.assertIsNotNone(result.validation_report)
        self.assertIsNotNone(result.artifact_store)
        self.assertGreater(len(result.audit_events), 0)

    def test_structured_pipeline_passes_with_golden_data(self) -> None:
        """structured_pipeline with golden Req/Spec/DSL must pass."""
        with TemporaryDirectory() as tmp:
            result = run_job(
                {
                    "mode": "structured_pipeline",
                    "requirement": golden_requirement(),
                    "specification": golden_specification(),
                    "dsl": golden_dsl(),
                    "traceability_id": "tr_job_test_structured",
                },
                output_dir=Path(tmp) / "out",
            )
        self.assertFalse(result.blocked, f"blocked: reason={result.reason_code} detail={result.detail}")
        self.assertEqual(result.state, "validation_passed")
        self.assertEqual(result.traceability_id, "tr_job_test_structured")

    def test_llm_pipeline_mode_is_blocked(self) -> None:
        """llm_pipeline mode must return blocked with UNSUPPORTED_MODE."""
        result = run_job({"mode": "llm_pipeline"})
        self.assertTrue(result.blocked)
        self.assertEqual(result.reason_code, "UNSUPPORTED_MODE")

    def test_invalid_mode_is_blocked(self) -> None:
        """Unknown mode must be blocked."""
        result = run_job({"mode": "fantasy_mode"})
        self.assertTrue(result.blocked)
        self.assertEqual(result.reason_code, "UNSUPPORTED_MODE")

    def test_structured_pipeline_rejects_missing_requirement(self) -> None:
        """structured_pipeline without requirement dict must block."""
        result = run_job({"mode": "structured_pipeline"})
        self.assertTrue(result.blocked)
        self.assertEqual(result.reason_code, "INVALID_REQUIREMENT")

    def test_structured_pipeline_rejects_invalid_requirement_schema(self) -> None:
        """structured_pipeline with invalid requirement schema must block."""
        result = run_job(
            {
                "mode": "structured_pipeline",
                "requirement": {"not": "valid"},
                "specification": golden_specification(),
                "dsl": golden_dsl(),
            }
        )
        self.assertTrue(result.blocked)
        self.assertEqual(result.reason_code, "REQUIREMENT_SCHEMA_FAILED")

    def test_structured_pipeline_rejects_invalid_specification_schema(self) -> None:
        """structured_pipeline with invalid specification schema must block."""
        result = run_job(
            {
                "mode": "structured_pipeline",
                "requirement": golden_requirement(),
                "specification": {"not": "valid"},
                "dsl": golden_dsl(),
            }
        )
        self.assertTrue(result.blocked)
        self.assertEqual(result.reason_code, "SPECIFICATION_SCHEMA_FAILED")

    def test_structured_pipeline_rejects_bad_dsl_ast(self) -> None:
        """structured_pipeline with DSL AST failure must block."""
        bad_dsl = dict(golden_dsl())
        bad_dsl["features"] = [{"op": "unsupported_op", "length_mm": 10, "width_mm": 10, "height_mm": 10}]
        result = run_job(
            {
                "mode": "structured_pipeline",
                "requirement": golden_requirement(),
                "specification": golden_specification(),
                "dsl": bad_dsl,
            }
        )
        self.assertTrue(result.blocked)
        self.assertEqual(result.reason_code, "DSL_AST_VALIDATION_FAILED")

    def test_fixture_pipeline_traceability_id_default(self) -> None:
        """fixture_pipeline must generate a default traceability_id."""
        with TemporaryDirectory() as tmp:
            result = run_job({"mode": "fixture_pipeline"}, output_dir=Path(tmp) / "out")
        self.assertTrue(result.traceability_id.startswith("tr_job_"))

    def test_cli_run_job_fixture_defaults(self) -> None:
        """CLI 'run-job' with no input must default to fixture_pipeline and pass."""
        proc = subprocess.run(
            [sys.executable, "-m", "cad_agent.cli", "run-job"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = json.loads(proc.stdout)
        self.assertIn("state", output)
        self.assertEqual(output.get("blocked"), False)
        self.assertEqual(output.get("state"), "validation_passed")

    def test_cli_run_job_with_input_file(self) -> None:
        """CLI 'run-job --input <file>' must read JSON input spec."""
        with TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            input_path.write_text(json.dumps({"mode": "fixture_pipeline", "traceability_id": "tr_job_cli_file"}))
            proc = subprocess.run(
                [sys.executable, "-m", "cad_agent.cli", "run-job", "--input", str(input_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        output = json.loads(proc.stdout)
        self.assertEqual(output.get("blocked"), False)
        self.assertEqual(output.get("state"), "validation_passed")
        self.assertEqual(output.get("traceability_id"), "tr_job_cli_file")

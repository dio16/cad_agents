from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cad_agent.phase2_pilot import (
    compare_phase_reports,
    route_model,
    run_phase2_pilot,
    validate_dfm_profile_against_spec,
    write_review_viewer,
)
from cad_agent.platform_poc import golden_specification, run_golden_pipeline


class Phase2PilotTest(unittest.TestCase):
    def test_dfm_am_catalog_validates_golden_specification(self) -> None:
        result = validate_dfm_profile_against_spec(golden_specification())
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["profile"]["profile_id"], "fdm_standard")

    def test_model_gateway_blocks_confidential_commercial_route(self) -> None:
        blocked = route_model("confidential", "commercial")
        self.assertEqual(blocked["status"], "fail")
        self.assertEqual(blocked["selected_route"], "onprem")
        allowed = route_model("public", "commercial")
        self.assertEqual(allowed["status"], "pass")

    def test_model_gateway_requires_approval_for_restricted_data(self) -> None:
        for classification in ["regulated", "export-controlled"]:
            blocked = route_model(classification, "commercial")
            self.assertEqual(blocked["status"], "fail")
            self.assertEqual(blocked["route_status"], "fail")
            self.assertEqual(blocked["approval_status"], "pending")
            self.assertFalse(blocked["approval_satisfied"])

            allowed_route = route_model(classification, "onprem")
            self.assertEqual(allowed_route["status"], "pending_approval")
            self.assertEqual(allowed_route["route_status"], "pass")
            self.assertEqual(allowed_route["selected_route"], "onprem")
            self.assertTrue(allowed_route["human_approval_required"])

    def test_version_compare_reports_changed_parameters(self) -> None:
        with TemporaryDirectory() as temp_dir:
            baseline = run_golden_pipeline(Path(temp_dir) / "baseline")
            revised = json.loads(json.dumps(baseline))
            revised["specification"]["parameter_table"]["wall_t"] = 5.0
            diff = compare_phase_reports(baseline, revised)
            self.assertEqual(diff["status"], "pass")
            self.assertIn("wall_t", diff["changed_parameters"])

    def test_review_viewer_escapes_inserted_values(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "review.html"
            result = write_review_viewer(
                output_path,
                {
                    "dsl": {"traceability_id": "<script>alert('x')</script>"},
                    "runtime": {"status": "<bad status>"},
                    "validation_report": {"pass": "<bad pass>"},
                },
                {"path": "<bad path>"},
                {"changed_parameters": {}},
            )
            html = Path(result["path"]).read_text(encoding="utf-8")
            self.assertNotIn("<script>", html)
            self.assertIn("&lt;script&gt;", html)

    def test_phase2_pilot_run_writes_artifacts_and_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "phase2"
            report = run_phase2_pilot(output_dir)
            self.assertEqual(report["status"], "pass")
            self.assertTrue((output_dir / "phase2_pilot_report.json").exists())
            self.assertTrue(Path(report["mesh_artifact"]["path"]).exists())
            self.assertTrue(Path(report["review_ui_artifact"]["path"]).exists())
            self.assertTrue(Path(report["audit_log"]["audit_path"]).exists())


if __name__ == "__main__":
    unittest.main()

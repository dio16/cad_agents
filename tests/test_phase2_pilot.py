from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cad_agent.phase2_pilot import (
    compare_phase_reports,
    golden_specification,
    route_model,
    run_phase2_pilot,
    validate_dfm_profile_against_spec,
)
from cad_agent.platform_poc import run_golden_pipeline


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

    def test_version_compare_reports_changed_parameters(self) -> None:
        with TemporaryDirectory() as temp_dir:
            baseline = run_golden_pipeline(Path(temp_dir) / "baseline")
            revised = json.loads(json.dumps(baseline))
            revised["specification"]["parameter_table"]["wall_t"] = 5.0
            diff = compare_phase_reports(baseline, revised)
            self.assertEqual(diff["status"], "pass")
            self.assertIn("wall_t", diff["changed_parameters"])

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

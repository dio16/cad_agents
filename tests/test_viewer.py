"""Tests for the standard HTML assembly viewer and the assembly pipeline integration."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from cad_agent.assembly_checks import AssemblyPart, BBox, check_interference
from cad_agent.platform_poc import run_assembly_pipeline
from cad_agent.viewer import write_assembly_viewer

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "gear_train_v1"

GEARS = [
    ("pinion1", "tr_dsl_gear_pinion1", "dsl_pinion1.json", 0.0, 0.0, 20.0, 0.0, 20.0),
    ("gear1", "tr_dsl_gear_gear1", "dsl_gear1.json", 60.0, 0.0, 40.0, 0.0, 20.0),
    ("pinion2", "tr_dsl_gear_pinion2", "dsl_pinion2.json", 60.0, 0.0, 20.0, 40.0, 60.0),
    ("gear2", "tr_dsl_gear_gear2", "dsl_gear2.json", 180.0, 0.0, 100.0, 40.0, 60.0),
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ViewerTest(TestCase):
    def test_write_assembly_viewer_creates_html_and_artifact(self):
        from cad_agent.viewer import box_mesh
        from types import SimpleNamespace

        parts = [
            SimpleNamespace(part_id="pinion1", color="#4e79a7", triangles=box_mesh(0, 0, 0, 40, 40, 20)),
            SimpleNamespace(part_id="gear1", color="#f28e2b", triangles=box_mesh(60, 0, 0, 100, 40, 20)),
        ]
        report = check_interference(
            [
                AssemblyPart("pinion1", "tr1", BBox(0, 0, 0, 40, 40, 20)),
                AssemblyPart("gear1", "tr2", BBox(60, 0, 0, 100, 40, 20)),
            ]
        )
        spec = {"unresolved_risks": ["surrogate geometry"]}
        requirement = {"product_type": "gear train", "functional_requirements": ["1:10 ratio"]}

        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "viewer.html"
            artifact = write_assembly_viewer(
                out, parts=parts, report=report, spec=spec, requirement=requirement, ratio=10.0
            )
            self.assertTrue(out.exists())
            html = out.read_text(encoding="utf-8")
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn("<canvas", html)
            self.assertIn("pinion1", html)
            self.assertIn("gear1", html)
            self.assertIn('"ratio": 10.0', html)
            self.assertIn('"status": "pass"', html)
            self.assertEqual(artifact["format"], "html")
            self.assertTrue(artifact["artifact_id"].startswith("art_"))
            self.assertTrue(artifact["artifact_hash"].startswith("sha256:"))

    def test_run_assembly_pipeline_emits_viewer_and_passes(self):
        requirement = _load(EXAMPLE / "requirement.json")
        specification = _load(EXAMPLE / "specification.json")
        gears = []
        for part_id, tr_id, dsl_file, cx, cy, r, zmin, zmax in GEARS:
            dsl = _load(EXAMPLE / dsl_file)
            gears.append(
                {"part_id": part_id, "traceability_id": tr_id, "dsl": dsl, "cx": cx, "cy": cy, "r": r, "zmin": zmin, "zmax": zmax}
            )

        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "artifacts"
            result = run_assembly_pipeline(
                gears,
                specification=specification,
                requirement=requirement,
                output_dir=out_dir,
            )
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["assembly"]["status"], "pass")
            self.assertEqual(result["ratio_check"]["computed_total_ratio"], 10.0)
            self.assertIsNotNone(result["viewer"])
            expected = out_dir / "assembly_viewer.html"
            self.assertTrue(expected.exists())
            self.assertEqual(result["viewer"]["path"], str(expected))
            self.assertIn("art_", result["viewer"]["artifact_id"])

"""Regression test for gear_train_v2 (changed dimensions).

Runs the assembly pipeline on a second gear train whose radii, thicknesses, and shaft
positions differ from gear_train_v1, and verifies that the emitted HTML viewer renders
EXACTLY the actual STL mesh placed at the assembly location (no convention assumptions
about how the runtime extrudes the cylinder). This guards the viewer-geometry fix
against dimension/placement changes: the viewer must match the STEP/STL artifact.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from cad_agent.platform_poc import run_assembly_pipeline
from cad_agent.schema_gate import validate_against_schema
from cad_agent.viewer import read_stl_triangles

EXAMPLE = Path(__file__).parent.parent / "examples" / "gear_train_v2"

GEAR_ROWS = [
    # part_id, traceability_id, dsl_file, cx, cy, r, zmin, zmax
    ("pinion1", "tr_dsl_gear_pinion1", "dsl_pinion1.json", 0.0, 0.0, 10.0, 0.0, 12.0),
    ("gear1", "tr_dsl_gear_gear1", "dsl_gear1.json", 35.0, 0.0, 25.0, 0.0, 12.0),
    ("pinion2", "tr_dsl_gear_pinion2", "dsl_pinion2.json", 35.0, 0.0, 12.0, 40.0, 48.0),
    ("gear2", "tr_dsl_gear_gear2", "dsl_gear2.json", 95.0, 0.0, 48.0, 40.0, 48.0),
]


def _load(name: str) -> dict:
    return json.loads((EXAMPLE / name).read_text(encoding="utf-8"))


def _stl_path_for(result: dict, part_id: str) -> Path:
    for gr in result["gears"]:
        if gr["part_id"] == part_id:
            for a in gr["artifacts"]:
                if a.endswith(".stl"):
                    return Path(a)
    raise AssertionError(f"no STL artifact for {part_id}")


def _expected_placed(stl_path: Path, cx: float, cy: float, zmin: float):
    """Expected (centroid, half_extents, triangle_count) after the pipeline's assembly placement."""
    tris = read_stl_triangles(stl_path)
    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    zs = [v[2] for t in tris for v in t]
    lmin = (min(xs), min(ys), min(zs))
    lmax = (max(xs), max(ys), max(zs))
    hx, hy, hz = (lmax[0] - lmin[0]) / 2, (lmax[1] - lmin[1]) / 2, (lmax[2] - lmin[2]) / 2
    lcx, lcy, lcz = (lmin[0] + lmax[0]) / 2, (lmin[1] + lmax[1]) / 2, (lmin[2] + lmax[2]) / 2
    dx = cx - lcx
    dy = cy - lcy
    dz = (zmin + hz) - lcz
    centroid = (lcx + dx, lcy + dy, lcz + dz)
    return centroid, (hx, hy, hz), len(tris)


def _run_pipeline() -> tuple[dict, dict, dict]:
    """Run the pipeline; return (result, viewer_data, expected_by_id).

    The STL artifact is read while the temp directory is still alive, so the
    expected placed geometry is captured before cleanup.
    """
    requirement = _load("requirement.json")
    specification = _load("specification.json")
    gears = []
    for part_id, tr_id, dsl_file, cx, cy, r, zmin, zmax in GEAR_ROWS:
        gears.append(
            {
                "part_id": part_id,
                "traceability_id": tr_id,
                "dsl": _load(dsl_file),
                "cx": cx,
                "cy": cy,
                "r": r,
                "zmin": zmin,
                "zmax": zmax,
            }
        )
    with tempfile.TemporaryDirectory() as tmp:
        result = run_assembly_pipeline(
            gears,
            specification=specification,
            requirement=requirement,
            output_dir=Path(tmp) / "artifacts",
        )
        html = Path(result["viewer"]["path"]).read_text(encoding="utf-8")
        m = re.search(r"const DATA = (\{.*?\});\nconst PARTS", html, re.S)
        assert m, "viewer DATA not found"
        data = json.loads(m.group(1))
        expected_by_id = {}
        for part_id, _tr, _dsl, cx, cy, _r, zmin, _zmax in GEAR_ROWS:
            stl = _stl_path_for(result, part_id)
            expected_by_id[part_id] = _expected_placed(stl, cx, cy, zmin)
    return result, data, expected_by_id


class TestGearTrainV2:
    def test_v2_pipeline_passes_and_viewer_matches_stl(self):
        requirement = _load("requirement.json")
        specification = _load("specification.json")

        schema_ok = all(
            c.status == "pass"
            for kind, doc in (("requirement", requirement), ("specification", specification))
            for c in validate_against_schema(doc, kind)
        )
        assert schema_ok, "schema gate failed"

        result, data, expected_by_id = _run_pipeline()
        assert result["status"] == "pass", result
        assert result["ratio_check"]["computed_total_ratio"] == 10.0, result["ratio_check"]

        by_id = {p["id"]: p for p in data["parts"]}
        assert set(by_id) == {row[0] for row in GEAR_ROWS}

        for part_id in by_id:
            exp_centroid, exp_half, stl_count = expected_by_id[part_id]
            tris = by_id[part_id]["triangles"]
            xs = [v[0] for t in tris for v in t]
            ys = [v[1] for t in tris for v in t]
            zs = [v[2] for t in tris for v in t]
            got_centroid = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))
            got_half = (
                (max(xs) - min(xs)) / 2,
                (max(ys) - min(ys)) / 2,
                (max(zs) - min(zs)) / 2,
            )

            assert all(abs(g - e) < 1.0 for g, e in zip(got_centroid, exp_centroid)), (
                part_id,
                got_centroid,
                exp_centroid,
            )
            assert all(abs(g - e) < 0.5 for g, e in zip(got_half, exp_half)), (
                part_id,
                got_half,
                exp_half,
            )
            # viewer renders every STL triangle verbatim
            assert len(tris) == stl_count, (part_id, len(tris), stl_count)
            assert len(tris) > 100, (part_id, len(tris))

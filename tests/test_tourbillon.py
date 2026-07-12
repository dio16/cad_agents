"""Tests for the tourbillon Mechanism DSL (CAD-FG-17).

Covers: per-op schema validation, per-op CAD runtime generation, the reserved
GEAR_GENERATION_FAILED contract error code, the tourbillon cage-containment
assembly constraint (pass + negative), and viewer STL fidelity via the assembly
pipeline.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from cad_agent.assembly_checks import BBox, AssemblyPart, check_tourbillon_constraints
from cad_agent.platform_poc import run_assembly_pipeline, run_cad_runtime
from cad_agent.schema_gate import validate_against_schema
from cad_agent.viewer import read_stl_triangles

EXAMPLE = Path(__file__).parent.parent / "examples" / "tourbillon"

PARTS = [
    # part_id, traceability_id, dsl_file, cx, cy, r, zmin, zmax
    ("fixed_wheel", "tr_dsl_tb_fixed_wheel", "dsl_fixed_wheel.json", 0.0, 0.0, 7.0, 0.0, 1.0),
    ("cage", "tr_dsl_tb_cage", "dsl_cage.json", 0.0, 0.0, 12.0, 3.0, 4.0),
    ("escape_wheel", "tr_dsl_tb_escape", "dsl_escape_wheel.json", 3.0, 0.0, 6.0, 6.75, 7.0),
    ("balance_wheel", "tr_dsl_tb_balance", "dsl_balance_wheel.json", -2.0, 0.0, 7.0, 8.25, 9.0),
    ("lever", "tr_dsl_tb_lever", "dsl_lever.json", 3.0, 0.0, 6.0, 9.25, 10.0),
    ("hairspring", "tr_dsl_tb_hairspring", "dsl_hairspring.json", 0.0, 0.0, 4.2, 10.25, 11.0),
    ("jewel", "tr_dsl_tb_jewel", "dsl_jewel.json", 0.0, 0.0, 1.5, 10.5, 12.0),
]

NEW_OPS = {
    "gear": {"op": "gear", "module_mm": "$m", "teeth": "$z", "thickness_mm": "$t", "bore_diameter_mm": "$b", "axis": "z", "positions_mm": [[0.0, 0.0]]},
    "escape_wheel": {"op": "escape_wheel", "teeth": "$z", "tip_radius_mm": "$ra", "thickness_mm": "$t", "bore_diameter_mm": "$b", "tooth_type": "club", "axis": "z", "positions_mm": [[0.0, 0.0]]},
    "balance_wheel": {"op": "balance_wheel", "outer_diameter_mm": "$od", "rim_width_mm": "$rw", "spokes": "$s", "thickness_mm": "$t", "bore_diameter_mm": "$b", "axis": "z", "positions_mm": [[0.0, 0.0]]},
    "lever": {"op": "lever", "length_mm": "$L", "width_mm": "$W", "thickness_mm": "$t", "fork_width_mm": "$fw", "pivot_diameter_mm": "$pd", "axis": "z", "positions_mm": [[0.0, 0.0]]},
    "cage": {"op": "cage", "outer_diameter_mm": "$od", "arm_count": "$a", "thickness_mm": "$t", "bore_diameter_mm": "$b", "bridge": True, "axis": "z", "positions_mm": [[0.0, 0.0]]},
    "hairspring": {"op": "hairspring", "outer_diameter_mm": "$od", "coils": "$co", "wire_diameter_mm": "$wd", "thickness_mm": "$t", "axis": "z", "positions_mm": [[0.0, 0.0]]},
    "jewel": {"op": "jewel", "diameter_mm": "$d", "thickness_mm": "$t", "axis": "z", "positions_mm": [[0.0, 0.0]]},
}

OP_PARAMS = {
    "gear": {"m": 2.0, "z": 30, "t": 3.0, "b": 4.0},
    "escape_wheel": {"z": 15, "ra": 6.0, "t": 1.5, "b": 1.0},
    "balance_wheel": {"od": 14.0, "rw": 2.0, "s": 3, "t": 1.0, "b": 1.0},
    "lever": {"L": 12.0, "W": 2.0, "t": 1.0, "fw": 2.0, "pd": 0.8},
    "cage": {"od": 20.0, "a": 3, "t": 3.0, "b": 4.0},
    "hairspring": {"od": 8.0, "co": 5.0, "wd": 0.3, "t": 0.5},
    "jewel": {"d": 3.0, "t": 2.0},
}


def _dsl(op: str) -> dict:
    return {
        "units": "mm",
        "parameters": OP_PARAMS[op],
        "traceability_id": "tr_dsl_test_" + op,
        "features": [NEW_OPS[op]],
        "derivative_outputs": ["step_ap242", "stl"],
    }


def _run_cad(op: str, tmp: Path) -> dict:
    return run_cad_runtime(_dsl(op), tmp / ("tr_dsl_test_" + op))


def test_each_new_op_validates_against_schema():
    for op in NEW_OPS:
        checks = list(validate_against_schema(_dsl(op), "parametric_dsl"))
        assert all(c.status == "pass" for c in checks), (op, [c.detail for c in checks])


def test_each_new_op_generates_cad():
    for op in NEW_OPS:
        with tempfile.TemporaryDirectory() as tmp:
            res = _run_cad(op, Path(tmp))
        assert res["status"] == "pass", (op, res)
        assert res.get("bbox_mm"), (op, res)
        assert any(a["format"] == "stl" for a in res["artifacts"]), (op, res)


def test_gear_generation_failed_error_code():
    bad = _dsl("gear")
    bad["parameters"] = {"m": 2.0, "z": 0, "t": 3.0, "b": 4.0}  # teeth=0 -> invalid
    with tempfile.TemporaryDirectory() as tmp:
        res = run_cad_runtime(bad, Path(tmp) / "tr_dsl_bad")
    assert res["status"] == "fail"
    assert res["reason_code"] == "GEAR_GENERATION_FAILED", res


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
    requirement = _load("requirement.json")
    specification = _load("specification.json")
    parts = []
    for part_id, tr_id, dsl_file, cx, cy, r, zmin, zmax in PARTS:
        parts.append(
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
            parts,
            specification=specification,
            requirement=requirement,
            output_dir=Path(tmp) / "artifacts",
        )
        html = Path(result["viewer"]["path"]).read_text(encoding="utf-8")
        m = re.search(r"const DATA = (\{.*?\});\nconst PARTS", html, re.S)
        assert m, "viewer DATA not found"
        data = json.loads(m.group(1))
        expected_by_id = {}
        for part_id, _tr, _dsl, cx, cy, _r, zmin, _zmax in PARTS:
            stl = _stl_path_for(result, part_id)
            expected_by_id[part_id] = _expected_placed(stl, cx, cy, zmin)
    return result, data, expected_by_id


def test_tourbillon_pipeline_passes_and_viewer_matches_stl():
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
    assert result["assembly"]["status"] == "pass", result["assembly"]

    by_id = {p["id"]: p for p in data["parts"]}
    assert set(by_id) == {row[0] for row in PARTS}

    for part_id in by_id:
        exp_centroid, exp_half, stl_count = expected_by_id[part_id]
        tris = by_id[part_id]["triangles"]
        xs = [v[0] for t in tris for v in t]
        ys = [v[1] for t in tris for v in t]
        zs = [v[2] for t in tris for v in t]
        got_centroid = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))
        got_half = ((max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2, (max(zs) - min(zs)) / 2)
        assert all(abs(g - e) < 1.0 for g, e in zip(got_centroid, exp_centroid)), (part_id, got_centroid, exp_centroid)
        assert all(abs(g - e) < 0.5 for g, e in zip(got_half, exp_half)), (part_id, got_half, exp_half)
        assert len(tris) == stl_count, (part_id, len(tris), stl_count)
        assert len(tris) > 100, (part_id, len(tris))


def _reconstruct_assembly_parts(result: dict) -> list[AssemblyPart]:
    placement = {row[0]: (row[3], row[4], row[6]) for row in PARTS}
    asm: list[AssemblyPart] = []
    for g in result["gears"]:
        cx, cy, zmin = placement[g["part_id"]]
        bb = g["bbox_mm"] or {}
        hx = float(bb.get("length", 0.0)) / 2.0
        hy = float(bb.get("width", 0.0)) / 2.0
        hz = float(bb.get("height", 0.0)) / 2.0
        asm.append(
            AssemblyPart(
                part_id=g["part_id"],
                traceability_id=g["traceability_id"],
                bbox=BBox(cx - hx, cy - hy, zmin, cx + hx, cy + hy, zmin + hz),
            )
        )
    return asm


def test_tourbillon_cage_containment_passes():
    result, _data, _exp = _run_pipeline()
    report = check_tourbillon_constraints(_reconstruct_assembly_parts(result))
    assert report.status == "pass", report.as_dict()
    assert not any(i.code == "ASSEMBLY_CONSTRAINT_FAILED" for i in report.issues)


def test_tourbillon_cage_containment_fails_when_escape_exceeds_cage():
    cage = AssemblyPart("cage", "tr_cage", BBox(-12.0, -12.0, 0.0, 12.0, 12.0, 1.0))
    escape = AssemblyPart("escape_wheel", "tr_escape", BBox(12.0, -6.0, 0.0, 18.0, 6.0, 1.0))
    report = check_tourbillon_constraints([cage, escape])
    assert report.status == "fail"
    assert any(i.code == "ASSEMBLY_CONSTRAINT_FAILED" for i in report.issues)


def test_tourbillon_constraint_missing_cage():
    wheel = AssemblyPart("balance_wheel", "tr_b", BBox(-7.0, -7.0, 0.0, 7.0, 7.0, 1.0))
    report = check_tourbillon_constraints([wheel])
    assert report.status == "fail"
    assert any(i.code == "TOURBILLON_NO_CAGE" for i in report.issues)


from cad_agent.assembly_checks import GearSpec, check_gear_mesh


def test_gear_mesh_passes_at_correct_centre_distance():
    """Two gears placed at the exact required centre distance must pass."""
    spec = {
        "a": GearSpec(module_mm=3.0, teeth=20),
        "b": GearSpec(module_mm=3.0, teeth=12),
    }
    # Required cd = 3*(20+12)/2 = 48 mm. Place b at x=48.
    a = AssemblyPart("a", "tr_a", BBox(-30.0, -10.0, 0.0, 30.0, 10.0, 8.0))
    b = AssemblyPart("b", "tr_b", BBox(30.0, -10.0, 0.0, 66.0, 10.0, 6.0))
    report = check_gear_mesh([a, b], spec, [("a", "b")])
    assert report.status == "pass", [i.message for i in report.issues]


def test_gear_mesh_fails_at_wrong_distance():
    """Two gears placed at an incorrect centre distance must fail."""
    spec = {
        "a": GearSpec(module_mm=3.0, teeth=20),
        "b": GearSpec(module_mm=3.0, teeth=12),
    }
    # Required cd = 48 mm. Place b at x=50 (off by 2 mm).
    a = AssemblyPart("a", "tr_a", BBox(-30.0, -10.0, 0.0, 30.0, 10.0, 8.0))
    b = AssemblyPart("b", "tr_b", BBox(32.0, -10.0, 0.0, 68.0, 10.0, 6.0))
    report = check_gear_mesh([a, b], spec, [("a", "b")], tolerance_mm=0.5)
    assert report.status == "fail"
    assert any(i.code == "GEAR_MESH_DISTANCE" for i in report.issues)


def test_gear_mesh_fails_on_module_mismatch():
    """Gears with different modules must fail even if at the right distance."""
    spec = {
        "a": GearSpec(module_mm=3.0, teeth=20),
        "b": GearSpec(module_mm=2.0, teeth=20),
    }
    a = AssemblyPart("a", "tr_a", BBox(-15.0, -5.0, 0.0, 15.0, 5.0, 8.0))
    b = AssemblyPart("b", "tr_b", BBox(25.0, -5.0, 0.0, 55.0, 5.0, 6.0))
    report = check_gear_mesh([a, b], spec, [("a", "b")])
    assert report.status == "fail"
    assert any(i.code == "GEAR_MESH_MODULE_MISMATCH" for i in report.issues)


def test_gear_mesh_fails_on_missing_spec():
    a = AssemblyPart("a", "tr_a", BBox(-10.0, -5.0, 0.0, 10.0, 5.0, 8.0))
    b = AssemblyPart("b", "tr_b", BBox(30.0, -5.0, 0.0, 50.0, 5.0, 6.0))
    report = check_gear_mesh([a, b], {}, [("a", "b")])
    assert report.status == "fail"
    assert any(i.code == "GEAR_MESH_MISSING_SPEC" for i in report.issues)

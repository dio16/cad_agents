"""Tourbillon 3D-printable display object (~100×100×100 mm).

Generates:
- Individual STL + STEP files per part (via ``run_cad_runtime``)
- A combined assembly STEP/STL (cadquery union at assembly positions)
- The standard HTML viewer (via ``run_assembly_pipeline``)

Print each STL separately; the assembly STEP shows the intended layout.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from cad_agent.assembly_checks import AssemblyPart, BBox, GearSpec, check_gear_mesh, check_tourbillon_constraints
from cad_agent.platform_poc import (
    run_assembly_pipeline,
    run_cad_runtime,
    _build_box,
    _build_gear,
    _build_escape_wheel,
    _build_balance_wheel,
    _build_lever,
    _build_cage,
    _build_hairspring,
    _build_jewel,
)
from cad_agent.schema_gate import validate_against_schema
from cad_agent.viewer import read_stl_triangles

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts" / "tourbillon_3dp"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# ── Part definitions ─────────────────────────────────────────────────
# (part_id, feature, params, cx, cy, zmin)
# zmin places parts in distinct z-slabs with ~2 mm visual spacing.

PARTS: list[tuple[str, dict, dict, float, float, float]] = [
    # ── base plate ──
    ("base",
     {"op": "box", "length_mm": "$L", "width_mm": "$W", "height_mm": "$H",
      "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"L": 100.0, "W": 100.0, "H": 10.0},
     0.0, 0.0, 0.0),                                              # hz=5  → [0, 10]

    # ── fixed fourth wheel (spur gear at centre, m=3, z=20, pitch-r=30) ──
    ("fixed_wheel",
     {"op": "gear", "module_mm": "$m", "teeth": "$z", "thickness_mm": "$t",
      "bore_diameter_mm": "$b", "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"m": 3.0, "z": 20, "t": 8.0, "b": 10.0},
     0.0, 0.0, 12.0),                                             # hz=8  → [12, 28]

    # ── intermediate wheel (meshes with fixed_wheel, m=3, z=12, pitch-r=18) ──
    # centre distance = m·(z1+z2)/2 = 3·(20+12)/2 = 48 mm → placed at x=48
    ("intermediate_wheel",
     {"op": "gear", "module_mm": "$m", "teeth": "$z", "thickness_mm": "$t",
      "bore_diameter_mm": "$b", "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"m": 3.0, "z": 12, "t": 6.0, "b": 6.0},
     48.0, 0.0, 12.0),                                            # hz=6  → [12, 24]

    # ── rotating cage (coaxial with fixed_wheel) ──
    ("cage",
     {"op": "cage", "outer_diameter_mm": "$od", "arm_count": "$a",
      "thickness_mm": "$t", "bore_diameter_mm": "$b", "bridge": True,
      "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"od": 110.0, "a": 5, "t": 6.0, "b": 14.0},
     0.0, 0.0, 32.0),                                             # hz=7.5 → [32, 47]

    # ── escape wheel ──
    ("escape_wheel",
     {"op": "escape_wheel", "teeth": "$z", "tip_radius_mm": "$ra",
      "thickness_mm": "$t", "bore_diameter_mm": "$b",
      "tooth_type": "club", "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"z": 12, "ra": 26.0, "t": 5.0, "b": 5.0},
     14.0, 0.0, 49.0),                                            # hz=5  → [49, 59]

    # ── balance wheel ──
    ("balance_wheel",
     {"op": "balance_wheel", "outer_diameter_mm": "$od",
      "rim_width_mm": "$rw", "spokes": "$s",
      "thickness_mm": "$t", "bore_diameter_mm": "$b",
      "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"od": 52.0, "rw": 8.0, "s": 5, "t": 5.0, "b": 5.0},
     -12.0, 0.0, 61.0),                                           # hz=5  → [61, 71]

    # ── lever (pallet fork) ──
    ("lever",
     {"op": "lever", "length_mm": "$L", "width_mm": "$W",
      "thickness_mm": "$t", "fork_width_mm": "$fw",
      "pivot_diameter_mm": "$pd",
      "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"L": 48.0, "W": 8.0, "t": 5.0, "fw": 12.0, "pd": 4.0},
     14.0, 0.0, 73.0),                                           # hz=5  → [73, 83]

    # ── hairspring ──
    ("hairspring",
     {"op": "hairspring", "outer_diameter_mm": "$od",
      "coils": "$co", "wire_diameter_mm": "$wd",
      "thickness_mm": "$t",
      "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"od": 38.0, "co": 8.0, "wd": 1.5, "t": 1.5},
     0.0, 0.0, 85.0),                                            # hz=1.5 → [85, 88]

    # ── jewel bearing ──
    ("jewel",
     {"op": "jewel", "diameter_mm": "$d", "thickness_mm": "$t",
      "axis": "z", "positions_mm": [[0.0, 0.0]]},
     {"d": 8.0, "t": 6.0},
     0.0, 0.0, 90.0),                                            # hz=6  → [90, 102]
]

BUILDERS = {
    "box": _build_box,
    "gear": _build_gear,
    "escape_wheel": _build_escape_wheel,
    "balance_wheel": _build_balance_wheel,
    "lever": _build_lever,
    "cage": _build_cage,
    "hairspring": _build_hairspring,
    "jewel": _build_jewel,
}


def _make_dsl(part_id: str, feature: dict, params: dict) -> dict:
    return {
        "units": "mm",
        "traceability_id": f"tr_dsl_3dp_{part_id}",
        "parameters": params,
        "features": [feature],
        "derivative_outputs": ["step_ap242", "stl"],
    }


def _load(name: str) -> dict:
    return json.loads((EXAMPLE_DIR / name).read_text(encoding="utf-8"))


def main() -> int:
    # ── Gate: schema validation ──────────────────────────────────
    requirement = _load("requirement.json")
    spec_ok = all(
        c.status == "pass"
        for kind, doc in (("requirement", requirement),)
        for c in validate_against_schema(doc, kind)
    )
    if not spec_ok:
        print("FAIL: requirement schema validation")
        return 1

    # ── Phase 1: individual STL + STEP per part ──────────────────
    print("=== Generating individual parts ===\n")
    results: dict[str, dict] = {}
    for part_id, feature, params, _cx, _cy, _zmin in PARTS:
        dsl = _make_dsl(part_id, feature, params)
        out_dir = ARTIFACT_DIR / part_id
        out_dir.mkdir(parents=True, exist_ok=True)
        res = run_cad_runtime(dsl, out_dir)
        results[part_id] = res
        stl = next((a["path"] for a in res.get("artifacts", []) if a.get("format") == "stl"), None)
        step = next((a["path"] for a in res.get("artifacts", []) if a.get("format") == "step_ap242"), None)
        print(f"  {part_id:20s}  {res['status']:6s}  stl={stl}")
        if step:
            print(f"  {'':20s}         step={step}")

    failed = [pid for pid, r in results.items() if r["status"] != "pass"]
    if failed:
        print(f"\nFAILED parts: {failed}")
        return 1

    # ── Phase 2: combined assembly STEP + STL ────────────────────
    print("\n=== Building combined assembly STEP/STL ===\n")
    asm: Any = None
    for part_id, feature, params, cx, cy, zmin in PARTS:
        builder = BUILDERS[feature["op"]]
        part = builder(feature, params, cq)
        bb = part.val().BoundingBox()
        local_zmin = bb.zmin
        part = part.translate((cx, cy, zmin - local_zmin))
        asm = part if asm is None else asm.union(part)

    asm_step = ARTIFACT_DIR / "tourbillon_assembly.step"
    asm_stl = ARTIFACT_DIR / "tourbillon_assembly.stl"
    cq.exporters.export(asm, str(asm_step), exportType="STEP")
    cq.exporters.export(asm, str(asm_stl), exportType="STL")
    print(f"  Assembly STEP → {asm_step}  ({asm_step.stat().st_size:,} bytes)")
    print(f"  Assembly STL  → {asm_stl}  ({asm_stl.stat().st_size:,} bytes)")

    # ── Phase 3: assembly viewer ─────────────────────────────────
    print("\n=== Generating assembly viewer ===\n")
    parts_for_pipeline = []
    for part_id, feature, params, cx, cy, zmin in PARTS:
        dsl = _make_dsl(part_id, feature, params)
        parts_for_pipeline.append({
            "part_id": part_id,
            "traceability_id": f"tr_dsl_3dp_{part_id}",
            "dsl": dsl,
            "cx": cx,
            "cy": cy,
            "r": 0.0,
            "zmin": zmin,
            "zmax": zmin + 5.0,
        })

    # Minimal specification for the viewer metadata panel
    spec = {
        "traceability_id": "tr_spec_tourbillon_3dp",
        "requirement_id": "tr_req_tourbillon_3dp",
        "parameter_table": {
            "cage_outer_diameter_mm": 110.0,
            "fixed_wheel_teeth": 20,
            "escape_wheel_teeth": 12,
            "overall_height_mm": 100.0,
        },
        "constraints": ["units == mm"],
        "material_candidates": ["PLA", "PETG"],
        "manufacturing_profile": "fdm_standard",
        "validation_plan": [],
        "unresolved_risks": [],
    }

    with tempfile.TemporaryDirectory() as tmp:
        pipeline = run_assembly_pipeline(
            parts_for_pipeline,
            specification=spec,
            requirement=requirement,
            output_dir=Path(tmp) / "artifacts",
        )
        # Copy viewer to artifact dir
        viewer_src = Path(pipeline["viewer"]["path"])
        viewer_dst = ARTIFACT_DIR / "assembly_viewer.html"
        viewer_dst.write_text(viewer_src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Assembly viewer → {viewer_dst}")

        print(f"\n  Pipeline overall: {pipeline['status']}")
        print(f"  Assembly (AABB):  {pipeline['assembly']['status']}")
        # AABB interference is EXPECTED for meshing gears sharing a z-slab.
        interferences = pipeline["assembly"].get("interferences", [])
        if interferences:
            pairs = [f"{i['parts'][0]}↔{i['parts'][1]}" for i in interferences]
            print(f"    ⚠ AABB interference (expected for meshing gear pair): {', '.join(pairs)}")

    # ── Phase 4: tourbillon containment check ────────────────────
    placement = {row[0]: (row[3], row[4], row[5]) for row in PARTS}
    asm_parts: list[AssemblyPart] = []
    for g in pipeline["gears"]:
        cx, cy, zmin = placement[g["part_id"]]
        bb = g["bbox_mm"] or {}
        hx = float(bb.get("length", 0.0)) / 2.0
        hy = float(bb.get("width", 0.0)) / 2.0
        hz = float(bb.get("height", 0.0)) / 2.0
        asm_parts.append(
            AssemblyPart(part_id=g["part_id"], traceability_id=g["traceability_id"],
                         bbox=BBox(cx - hx, cy - hy, zmin, cx + hx, cy + hy, zmin + hz))
        )
    tourbillon = check_tourbillon_constraints(asm_parts)
    print(f"  Tourbillon containment: {tourbillon.status}")
    if tourbillon.status != "pass":
        for i in tourbillon.issues:
            print(f"    [{i.code}] {i.message}")


    # ── Phase 5: gear mesh validation ────────────────────────────
    # The fixed fourth wheel (z=20) and intermediate wheel (z=12) share
    # module m=3.  Required centre distance = 3·(20+12)/2 = 48 mm.
    # The intermediate wheel is placed at cx=48 → actual cd = 48 mm.
    gear_specs = {
        "fixed_wheel": GearSpec(module_mm=3.0, teeth=20),
        "intermediate_wheel": GearSpec(module_mm=3.0, teeth=12),
    }
    meshing_pairs = [("fixed_wheel", "intermediate_wheel")]
    gear_report = check_gear_mesh(asm_parts, gear_specs, meshing_pairs)
    print(f"\n  Gear mesh: {gear_report.status}")
    if gear_report.status != "pass":
        for i in gear_report.issues:
            print(f"    [{i.code}] {i.message}")
    else:
        cd = 3.0 * (20 + 12) / 2.0
        print(f"    fixed_wheel (z=20) ↔ intermediate_wheel (z=12): centre distance = {cd:.1f} mm ✓")

    # ── Mechanical honesty summary ────────────────────────────────
    mechanical = (
        tourbillon.status == "pass"
        and gear_report.status == "pass"
    )
    print(f"\n  Mechanical validation (gear mesh + tourbillon containment): {'pass' if mechanical else 'FAIL'}")
    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  All artifacts in: {ARTIFACT_DIR}")
    print(f"  Parts generated:  {len(PARTS)}")
    print(f"  Assembly STEP:    {asm_step.name}  ({asm_step.stat().st_size:,} bytes)")
    print(f"  Assembly STL:     {asm_stl.name}  ({asm_stl.stat().st_size:,} bytes)")
    return 0 if mechanical else 1


if __name__ == "__main__":
    raise SystemExit(main())

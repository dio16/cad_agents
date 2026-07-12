"""Gear-train test case driver (example/gear_train_v1).

Design: 1:10 parallel-axis compound gear train.
  Stage 1 (spur):    pinion 20T -> gear 40T   (ratio 2:1)
  Stage 2 (helical): pinion 20T -> gear 100T  (ratio 5:1)
  Total = 2 * 5 = 10:1, all three shaft axes parallel (z).

This exercises the deterministic surrogate CAD path. The Mechanism DSL allowlist is
box / cylinder / through_hole + shaft; `gear` is NOT an approved operation, so each
gear blank is modeled as a `cylinder`. This is NOT real involute gear geometry; true
gear CAD requires a new approved DSL operation (human/reviewer approval + contract update).
"""
from __future__ import annotations

import json
from pathlib import Path

from cad_agent.assembly_checks import AssemblyPart, BBox, check_interference
from cad_agent.platform_poc import contract_status, run_cad_runtime, validate_parametric_dsl_ast
from cad_agent.schema_gate import validate_against_schema

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts" / "gear_train_v1"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# part_id, traceability_id, dsl filename, (cx, cy) center mm, pitch radius mm, z-min mm, z-max mm
GEARS = [
    ("pinion1", "tr_dsl_gear_pinion1", "dsl_pinion1.json", 0.0, 0.0, 20.0, 0.0, 20.0),
    ("gear1", "tr_dsl_gear_gear1", "dsl_gear1.json", 60.0, 0.0, 40.0, 0.0, 20.0),
    ("pinion2", "tr_dsl_gear_pinion2", "dsl_pinion2.json", 60.0, 0.0, 20.0, 40.0, 60.0),
    ("gear2", "tr_dsl_gear_gear2", "dsl_gear2.json", 180.0, 0.0, 100.0, 40.0, 60.0),
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    results: dict = {"example": "gear_train_v1", "gears": [], "assembly": {}, "ratio_check": {}, "schema_checks": {}}

    requirement = load(EXAMPLE_DIR / "requirement.json")
    specification = load(EXAMPLE_DIR / "specification.json")
    results["schema_checks"]["requirement"] = [c.status for c in validate_against_schema(requirement, "requirement")]
    results["schema_checks"]["specification"] = [c.status for c in validate_against_schema(specification, "specification")]

    parts: list[AssemblyPart] = []
    for part_id, tr_id, dsl_file, cx, cy, r, zmin, zmax in GEARS:
        dsl = load(EXAMPLE_DIR / dsl_file)
        ast = validate_parametric_dsl_ast(dsl)
        ast_status = contract_status(ast)
        runtime = run_cad_runtime(dsl, ARTIFACT_DIR / tr_id)
        parts.append(
            AssemblyPart(
                part_id=part_id,
                traceability_id=tr_id,
                bbox=BBox(cx - r, cy - r, zmin, cx + r, cy + r, zmax),
            )
        )
        results["gears"].append(
            {
                "part_id": part_id,
                "traceability_id": tr_id,
                "dsl_ast_status": ast_status,
                "runtime_status": runtime.get("status"),
                "bbox_mm": runtime.get("bbox_mm"),
                "volume_mm3": runtime.get("volume_mm3"),
                "artifacts": [a.get("path") for a in runtime.get("artifacts", [])],
            }
        )

    report = check_interference(parts)
    results["assembly"] = {
        "status": report.status,
        "analysis_scope": report.analysis_scope,
        "interferences": [
            {"parts": (i.part_a, i.part_b), "overlap_mm": i.overlap_mm} for i in report.interferences
        ],
        "separations": [
            {"parts": (s.part_a, s.part_b), "distance_mm": s.distance_mm, "gap_axis": s.gap_axis}
            for s in report.separations
        ],
        "adjacent": [{"parts": (a.part_a, a.part_b), "gap_axis": a.gap_axis} for a in report.adjacent_within_tolerance],
    }

    pt = specification["parameter_table"]
    computed = (pt["gear1_teeth"] / pt["pinion1_teeth"]) * (pt["gear2_teeth"] / pt["pinion2_teeth"])
    results["ratio_check"] = {
        "specified_total_ratio": pt["total_ratio"],
        "computed_total_ratio": computed,
        "stage1_ratio": pt["gear1_teeth"] / pt["pinion1_teeth"],
        "stage2_ratio": pt["gear2_teeth"] / pt["pinion2_teeth"],
        "pass": abs(computed - pt["total_ratio"]) < 1e-9,
    }

    overall = (
        all(s == "pass" for s in results["schema_checks"]["requirement"])
        and all(s == "pass" for s in results["schema_checks"]["specification"])
        and all(g["dsl_ast_status"] == "pass" and g["runtime_status"] == "pass" for g in results["gears"])
        and report.status == "pass"
        and results["ratio_check"]["pass"]
    )
    results["overall_status"] = "pass" if overall else "fail"

    out_path = EXAMPLE_DIR / "gear_train_validation_report.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())

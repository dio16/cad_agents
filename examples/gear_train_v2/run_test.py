"""Gear-train test case driver (example/gear_train_v2) — changed dimensions.

Design: 1:10 parallel-axis compound gear train with DIFFERENT dimensions from v1
to exercise the viewer/placement logic on new geometry:
  Stage 1 (spur):    pinion 10T -> gear 25T   (ratio 2.5:1, r 10/25, h 12)
  Stage 2 (helical): pinion 12T -> gear 48T   (ratio 4:1,   r 12/48, h 8)
  Total = 2.5 * 4 = 10:1, three parallel shaft axes (x = 0, 35, 95).

This reuses the deterministic surrogate CAD path and emits the STANDARD HTML
assembly viewer (``assembly_viewer.html`` in the artifact directory). Each part is
rendered from its actual STL mesh placed at the assembly location, so the viewer must
reflect these changed dimensions/placement. The Mechanism DSL allowlist is
box / cylinder / through_hole + shaft; `gear` is NOT an approved operation, so each
gear blank is modeled as a `cylinder`.
"""
from __future__ import annotations

import json
from pathlib import Path

from cad_agent.platform_poc import run_assembly_pipeline
from cad_agent.schema_gate import validate_against_schema

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts" / "gear_train_v2"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# part_id, traceability_id, dsl filename, (cx, cy) center mm, pitch radius mm, z-min mm, z-max mm
GEARS = [
    ("pinion1", "tr_dsl_gear_pinion1", "dsl_pinion1.json", 0.0, 0.0, 10.0, 0.0, 12.0),
    ("gear1", "tr_dsl_gear_gear1", "dsl_gear1.json", 35.0, 0.0, 25.0, 0.0, 12.0),
    ("pinion2", "tr_dsl_gear_pinion2", "dsl_pinion2.json", 35.0, 0.0, 12.0, 40.0, 48.0),
    ("gear2", "tr_dsl_gear_gear2", "dsl_gear2.json", 95.0, 0.0, 48.0, 40.0, 48.0),
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    requirement = load(EXAMPLE_DIR / "requirement.json")
    specification = load(EXAMPLE_DIR / "specification.json")
    schema_checks = {
        "requirement": [c.status for c in validate_against_schema(requirement, "requirement")],
        "specification": [c.status for c in validate_against_schema(specification, "specification")],
    }

    gears = []
    for part_id, tr_id, dsl_file, cx, cy, r, zmin, zmax in GEARS:
        dsl = load(EXAMPLE_DIR / dsl_file)
        gears.append(
            {"part_id": part_id, "traceability_id": tr_id, "dsl": dsl, "cx": cx, "cy": cy, "r": r, "zmin": zmin, "zmax": zmax}
        )

    pipeline = run_assembly_pipeline(
        gears,
        specification=specification,
        requirement=requirement,
        output_dir=ARTIFACT_DIR,
    )

    rc = pipeline["ratio_check"]
    ratio_pass = rc["computed_total_ratio"] is not None and abs(rc["computed_total_ratio"] - (rc["specified_total_ratio"] or 0)) < 1e-9

    results = {"example": "gear_train_v2", "schema_checks": schema_checks, **pipeline}
    results["ratio_check"]["pass"] = ratio_pass

    overall = (
        all(s == "pass" for s in schema_checks["requirement"])
        and all(s == "pass" for s in schema_checks["specification"])
        and pipeline["status"] == "pass"
        and ratio_pass
    )
    results["overall_status"] = "pass" if overall else "fail"

    out_path = EXAMPLE_DIR / "gear_train_validation_report.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())

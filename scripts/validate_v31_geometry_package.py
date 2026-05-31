from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_geometry_summary.json"
OUT = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_geometry_package_validation.json"
REQUIRED = {
    "11_ratchet_winding_wheel_108t_v31",
    "12_ratchet_pawl_v31",
    "13_slip_clutch_disc_v31",
    "14_spring_barrel_housing_v31",
    "15_spring_barrel_output_gear_36t_v31",
    "20_vertical_lift_shaft_ref_v31",
}


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    parts = {item["name"]: item for item in summary["parts"]}
    single_solid = []
    for item in parts.values():
        shape = cq.importers.importStep(item["step"])
        single_solid.append({"name": item["name"], "solid_count": len(shape.val().Solids())})
    checks = [
        {"name": "required V31 power-path solids exist", "status": "pass" if REQUIRED.issubset(parts) else "fail", "missing": sorted(REQUIRED - set(parts))},
        {"name": "all generated STEP files import as single solids", "status": "pass" if all(item["solid_count"] == 1 for item in single_solid) else "fail", "parts": single_solid},
        {"name": "geometry summary is explicitly non-completion", "status": "pass" if "completion not yet claimed" in summary["claim"] else "fail"},
    ]
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": summary.get("generation_id"),
        "status": status,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

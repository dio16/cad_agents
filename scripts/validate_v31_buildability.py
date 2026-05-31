from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v31_buildability_contract.json"
OUT = ROOT / "reports" / "v31_buildability_validation.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    checks = [
        {"name": "minimum wall thickness >= 2.4 mm", "status": "pass" if contract["minimum_wall_thickness_mm"] >= 2.4 else "fail"},
        {"name": "minimum running clearance >= 0.2 mm", "status": "pass" if contract["minimum_running_clearance_mm"] >= 0.2 else "fail"},
        {"name": "critical shafts have two-point support", "status": "pass" if {"winding_arbor", "spring_barrel_axis", "vertical_lift_shaft"}.issubset(contract["two_point_support_roles"]) else "fail"},
        {"name": "support stacks define shaft, seat, and axial retention", "status": "pass" if all(stack["shaft_diameter_mm"] == 3 and stack["support_count"] >= 2 and stack["seat_type"] and set(stack["axial_retention"]) >= {"washer", "shaft_collar"} for stack in contract["support_stacks"].values()) else "fail"},
        {"name": "assembly access remains explicit", "status": "pass" if len(contract["assembly_access"]) >= 3 else "fail"},
    ]
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

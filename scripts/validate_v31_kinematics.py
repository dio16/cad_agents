from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v31_kinematic_contract.json"
OUT = ROOT / "reports" / "v31_kinematic_validation.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    checks = []
    for mesh in contract["meshes"]:
        expected = mesh["driver_pitch_radius_mm"] + mesh["driven_pitch_radius_mm"]
        checks.append({
            "name": f"{mesh['name']} center distance closes",
            "status": "pass" if math.isclose(expected, mesh["center_distance_mm"], abs_tol=1e-9) else "fail",
            "expected_mm": expected,
            "actual_mm": mesh["center_distance_mm"],
        })
        checks.append({
            "name": f"{mesh['name']} avoids low-tooth pinion",
            "status": "pass" if min(mesh["driver_teeth"], mesh["driven_teeth"]) >= contract["minimum_pinion_teeth"] else "fail",
        })
        checks.append({
            "name": f"{mesh['name']} clears the 20deg no-undercut threshold",
            "status": "pass" if min(mesh["driver_teeth"], mesh["driven_teeth"]) >= contract["minimum_no_undercut_teeth_20deg"] else "fail",
        })
    spatial = contract["spatial_transition"]
    checks.append({
        "name": "spatial transition changes height",
        "status": "pass" if spatial["to_z_mm"] > spatial["from_z_mm"] else "fail",
        "from_z_mm": spatial["from_z_mm"],
        "to_z_mm": spatial["to_z_mm"],
    })
    checks.append({
        "name": "backlash assumption exists",
        "status": "pass" if contract["backlash_allowance_mm"] > 0 else "fail",
    })
    checks.append({
        "name": "tip/root clearance assumption exists",
        "status": "pass" if contract["minimum_tip_root_clearance_mm"] >= 0.2 else "fail",
    })
    checks.append({
        "name": "profile shift decision is explicit",
        "status": "pass" if contract["profile_shift_required"] is False else "fail",
    })
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

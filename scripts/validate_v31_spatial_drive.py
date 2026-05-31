from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KIN = ROOT / "reports" / "v31_kinematic_validation.json"
ROLE = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_role_manifest_validation.json"
SUMMARY = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_geometry_summary.json"
OUT = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_spatial_drive_audit.json"


def main() -> int:
    kin = json.loads(KIN.read_text(encoding="utf-8"))
    role = json.loads(ROLE.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    parts = {item["name"]: item for item in summary["parts"]}
    shaft = parts["20_vertical_lift_shaft_ref_v31"]["bbox_mm"]["z"]
    checks = [
        {"name": "kinematic contract passes", "status": "pass" if kin.get("status") == "pass" else "fail"},
        {"name": "role manifest exposes the vertical lift", "status": "pass" if role.get("status") == "pass" else "fail"},
        {"name": "vertical shaft spans lower and upper planes", "status": "pass" if shaft[0] <= 8 and shaft[1] >= 68 else "fail", "shaft_z": shaft},
        {"name": "upper transfer pinion exists", "status": "pass" if "17_upper_transfer_pinion_18t_v31" in parts else "fail"},
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

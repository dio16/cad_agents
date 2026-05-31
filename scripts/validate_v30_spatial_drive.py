from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
SUMMARY = PACKAGE / "v30_package_summary.json"
TRACE = PACKAGE / "v30_contract_traceability_audit.json"
MOTION = PACKAGE / "v30_sampled_motion_audit.json"
OUT = PACKAGE / "v30_spatial_drive_audit.json"


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    trace = json.loads(TRACE.read_text(encoding="utf-8")) if TRACE.exists() else {"status": "missing"}
    motion = json.loads(MOTION.read_text(encoding="utf-8")) if MOTION.exists() else {"status": "missing"}
    parts = {item["name"]: item for item in summary["parts"]}
    shaft = parts["18_vertical_lift_shaft_ref_v30"]["bbox_mm"]["z"]
    checks = [
        {"name": "vertical lift shaft exists", "status": "pass" if "18_vertical_lift_shaft_ref_v30" in parts else "fail"},
        {"name": "shaft spans lower and upper planes", "status": "pass" if shaft[0] <= 8 and shaft[1] >= 68 else "fail", "shaft_z": shaft},
        {"name": "upper transfer pinion exists", "status": "pass" if "14_upper_transfer_pinion_18t_v30" in parts else "fail"},
        {"name": "spatial-drive design handoff passes", "status": "pass" if trace.get("status") == "pass" else "fail"},
        {"name": "full-system sampled motion proves transfer across height", "status": "pass" if motion.get("status") == "pass" else "fail"},
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "generation_id": summary.get("generation_id"), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

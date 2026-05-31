from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
SUMMARY = PACKAGE / "v30_package_summary.json"
ROLE_MANIFEST = PACKAGE / "v30_role_manifest.json"
VISIBILITY = PACKAGE / "v30_visibility_audit.json"
OUT = PACKAGE / "v30_object_value_audit.json"


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    role_manifest = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8")) if ROLE_MANIFEST.exists() else {"status": "missing"}
    visibility = json.loads(VISIBILITY.read_text(encoding="utf-8")) if VISIBILITY.exists() else {"status": "missing"}
    parts = {item["name"]: item for item in summary["parts"]}
    checks = [
        {"name": "large macro winding element exists", "status": "pass" if "11_visible_winding_drum_gear_108t_v30" in parts else "fail"},
        {"name": "elevated fine-motion core exists", "status": "pass" if "05_rotating_carrier_drive_gear_v30" in parts and "08_escape_wheel_15t_v30" in parts else "fail"},
        {"name": "layered motion hierarchy exists", "status": "pass" if {"11_visible_winding_drum_gear_108t_v30", "18_vertical_lift_shaft_ref_v30", "08_escape_wheel_15t_v30"}.issubset(parts) else "fail"},
        {"name": "role manifest proves visible moving roles", "status": "pass" if role_manifest.get("status") == "pass" else "fail"},
        {"name": "hero-view / sampled visibility evidence passes", "status": "pass" if visibility.get("status") == "pass" else "fail"},
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "generation_id": summary.get("generation_id"), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

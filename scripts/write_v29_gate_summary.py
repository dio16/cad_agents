from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v29_sculpture_package"
OUT = PACKAGE / "v29_gate_summary.json"


def load(name: str) -> dict:
    path = PACKAGE / name
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    package = load("v29_package_validation.json")
    motion = load("v29_motion_validation.json")
    winding = load("v29_stationary_winding_audit.json")
    spatial = load("v29_spatial_drive_audit.json")
    object_value = load("v29_object_value_audit.json")
    mechanical_truth = load("v29_mechanical_truth_audit.json")
    viewer = load("v29_wsl_http_viewer_smoke.json")
    deliverable = load("v29_user_deliverable_validation.json")
    checks = [
        {"name": "package validation passes", "status": "pass" if package.get("status") == "pass" else "fail"},
        {"name": "motion validation passes", "status": "pass" if motion.get("status") == "pass" else "fail"},
        {"name": "stationary winding evidence passes", "status": "pass" if winding.get("status") == "pass" else "fail"},
        {"name": "spatial drive evidence passes", "status": "pass" if spatial.get("status") == "pass" else "fail"},
        {"name": "object value evidence passes", "status": "pass" if object_value.get("status") == "pass" else "fail"},
        {"name": "mechanical truth evidence passes", "status": "pass" if mechanical_truth.get("status") == "pass" else "fail"},
        {"name": "continuous viewer smoke passes", "status": "pass" if viewer.get("status") == "pass" else "fail"},
        {"name": "user deliverable passes", "status": "pass" if deliverable.get("status") == "pass" else "fail"},
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "blocked"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "completion_wording": (
            "blocked: V29 object-level evidence has not fully passed"
            if status != "pass"
            else "V29 object-level evidence passes for a stationary-autonomous-winding spatial kinetic sculpture object candidate with continuous local fallback motion and a demonstrative non-regulating escapement"
        ),
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

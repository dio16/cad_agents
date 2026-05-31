from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_role_manifest.json"
OUT = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_role_manifest_validation.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    roles = manifest["roles"]
    visible = manifest["visible_moving_roles"]
    complete = [
        role for role in visible
        if {"parent", "support", "motion", "axis"}.issubset(roles.get(role, {}))
        and {"name", "origin_mm", "direction", "frame"}.issubset(roles[role]["axis"])
    ]
    checks = [
        {"name": "every visible moving role has role metadata", "status": "pass" if set(complete) == set(visible) else "fail", "complete_roles": complete},
        {"name": "spatial lift role exists", "status": "pass" if "vertical_lift_shaft" in roles else "fail"},
        {"name": "autonomous winding roles exist", "status": "pass" if {"motor_pinion", "ratchet_winding_wheel", "spring_barrel_output"}.issubset(roles) else "fail"},
    ]
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": manifest.get("generation_id"),
        "status": status,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

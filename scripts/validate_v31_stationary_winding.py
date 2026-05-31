from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POWER = ROOT / "reports" / "v31_power_path_validation.json"
ROLE = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_role_manifest_validation.json"
SUMMARY = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_geometry_summary.json"
OUT = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_stationary_winding_audit.json"


def main() -> int:
    power = json.loads(POWER.read_text(encoding="utf-8"))
    role = json.loads(ROLE.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    names = {part["name"] for part in summary["parts"]}
    checks = [
        {"name": "power-path feasibility passes", "status": "pass" if power.get("status") == "pass" else "fail"},
        {"name": "winding roles are present in the role manifest", "status": "pass" if role.get("status") == "pass" else "fail"},
        {"name": "ratchet / clutch / barrel solids exist", "status": "pass" if {"11_ratchet_winding_wheel_108t_v31", "12_ratchet_pawl_v31", "13_slip_clutch_disc_v31", "14_spring_barrel_housing_v31", "15_spring_barrel_output_gear_36t_v31"}.issubset(names) else "fail"},
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

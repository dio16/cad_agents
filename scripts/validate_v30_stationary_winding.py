from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
SUMMARY = PACKAGE / "v30_package_summary.json"
TRACE = PACKAGE / "v30_contract_traceability_audit.json"
OUT = PACKAGE / "v30_stationary_winding_audit.json"


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    trace = json.loads(TRACE.read_text(encoding="utf-8")) if TRACE.exists() else {"status": "missing"}
    parts = {item["name"] for item in summary["parts"]}
    checks = [
        {"name": "motor pinion exists", "status": "pass" if "10_motor_pinion_18t_v30" in parts else "fail"},
        {"name": "visible winding drum exists", "status": "pass" if "11_visible_winding_drum_gear_108t_v30" in parts else "fail"},
        {"name": "spring barrel output exists", "status": "pass" if "12_spring_barrel_output_gear_36t_v30" in parts else "fail"},
        {"name": "motor-to-drum-to-barrel path exists", "status": "pass" if {"10_motor_pinion_18t_v30", "11_visible_winding_drum_gear_108t_v30", "12_spring_barrel_output_gear_36t_v30"}.issubset(parts) else "fail"},
        {"name": "autonomous winding claim is backed by a passed design handoff", "status": "pass" if trace.get("status") == "pass" else "fail"},
        {"name": "winding control / reverse-flow / overload evidence exists", "status": "fail", "reason": "No V30 winding-control evidence artifact exists yet."},
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "generation_id": summary.get("generation_id"), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

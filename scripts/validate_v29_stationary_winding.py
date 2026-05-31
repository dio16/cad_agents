from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POWER = ROOT / "manifests" / "tourbillon_v29_power_path_feasibility_contract.json"
PACKAGE = ROOT / "reports" / "fabrication_v29_sculpture_package"
SUMMARY = PACKAGE / "v29_package_summary.json"
OUT = PACKAGE / "v29_stationary_winding_audit.json"


def main() -> int:
    power = json.loads(POWER.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    part_names = {item["name"] for item in summary["parts"]}
    with (PACKAGE / "purchased_parts.csv").open(encoding="utf-8") as f:
        purchased = list(csv.DictReader(f))
    purchased_items = {row["item"] for row in purchased}
    checks = [
        {
            "name": "powered winding path closes before display output",
            "status": "pass"
            if [step["name"] for step in power["winding_path"]] == ["motor_to_winding_drum", "drum_to_barrel"]
            else "fail",
        },
        {
            "name": "visible drum and barrel are generated",
            "status": "pass"
            if {"02_visible_winding_drum_v29", "03_spring_barrel_housing_v29"}.issubset(part_names)
            else "fail",
        },
        {
            "name": "motor and torsion spring are in purchased BOM",
            "status": "pass"
            if {"20D 313:1 12V gearmotor family", "LTML200Y 02 M torsion spring or equivalent"}.issubset(purchased_items)
            else "fail",
        },
        {
            "name": "control closure exists",
            "status": "pass"
            if {"recharge_trigger", "stop_trigger", "overwind_protection", "reverse_flow_protection"}.issubset(power["control_concept"])
            else "fail",
        },
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "evidence_kind": "contract_plus_generated_package",
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

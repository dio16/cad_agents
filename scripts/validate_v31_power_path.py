from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v31_power_path_contract.json"
OUT = ROOT / "reports" / "v31_power_path_validation.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    reserve = contract["motor_available_torque_nm"] / contract["required_carrier_torque_nm"]
    holdover = contract["barrel_stored_energy_j"] / contract["required_output_power_w"]
    controls = contract["controls"]
    barrel = contract["spring_barrel"]
    checks = [
        {"name": "torque reserve >= 5x", "status": "pass" if reserve >= 5 else "fail", "reserve_ratio": reserve},
        {"name": "holdover target closes", "status": "pass" if holdover >= contract["target_holdover_s"] else "fail", "holdover_s": holdover},
        {"name": "winding control chain defined", "status": "pass" if controls["ratchet"] and controls["one_way_clutch"] and bool(controls["overwind_protection"]) else "fail"},
        {"name": "overwind protection is selected, not deferred", "status": "pass" if controls["overwind_protection"] == "slip_clutch" and controls["slip_clutch_release_torque_nm"] >= contract["motor_available_torque_nm"] else "fail"},
        {"name": "spring barrel packaging is dimensioned", "status": "pass" if barrel["outer_diameter_mm"] > barrel["usable_inner_diameter_mm"] > barrel["arbor_diameter_mm"] and barrel["usable_turns"] >= 3 and barrel["packaging_margin_mm"] >= 2 else "fail"},
    ]
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

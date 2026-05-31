from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_power_path_feasibility_contract.json"
OUT = ROOT / "reports" / "v29_power_path_feasibility_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    contract = load(CONTRACT)
    motor = contract["motor_candidate"]
    spring = contract["spring_candidate"]
    budget = contract["derived_budget"]
    control = contract["control_concept"]
    checks: list[dict] = []
    add(checks, "all source contracts exist", all((ROOT / p).exists() for p in contract["source_contracts"]))
    add(checks, "20D motor fits concept chamber", motor["body_envelope_mm"][0] <= 25 and motor["body_envelope_mm"][2] <= 50)
    add(checks, "spring fits storage barrel budget", spring["outside_diameter_mm"] <= 36 and spring["body_length_mm"] <= 28)
    add(checks, "winding torque margin exceeds 1.5x working upper torque", budget["winding_torque_margin"] >= 1.5, winding_torque_margin=budget["winding_torque_margin"])
    add(checks, "stored energy covers 60 s design holdover with losses", budget["energy_margin"] >= 1.0, energy_margin=budget["energy_margin"])
    add(
        checks,
        "winding control path is explicit",
        all(control.get(key) for key in ("recharge_trigger", "stop_trigger", "overwind_protection", "reverse_flow_protection")),
        control=control,
    )
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_contract": str(CONTRACT),
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

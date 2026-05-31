from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWEEP = ROOT / "reports" / "v31_internal_feasibility_sweep_validation.json"
OUT = ROOT / "reports" / "v31_selected_design_feasibility_validation.json"
SOURCES = {
    "sweep": ROOT / "reports" / "v31_internal_feasibility_sweep_validation.json",
    "power_path": ROOT / "reports" / "v31_power_path_validation.json",
    "kinematics": ROOT / "reports" / "v31_kinematic_validation.json",
    "buildability": ROOT / "reports" / "v31_buildability_validation.json",
    "object_value_contract": ROOT / "reports" / "v31_object_value_contract_validation.json",
}


def main() -> int:
    reports = {name: json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"status": "missing"} for name, path in SOURCES.items()}
    checks = [
        {"name": f"{name} validation passes", "status": "pass" if report.get("status") == "pass" else "fail", "source": str(SOURCES[name])}
        for name, report in reports.items()
    ]
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "claim": "feasible selected design" if status == "pass" else "selected concept only",
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "v29_selected_design_feasibility_validation.json"
SOURCES = {
    "selected_concept": ROOT / "reports" / "v29_selected_concept_contract_validation.json",
    "power_path": ROOT / "reports" / "v29_power_path_feasibility_validation.json",
    "kinematics": ROOT / "reports" / "v29_kinematic_dimension_contract_validation.json",
    "hero_view": ROOT / "reports" / "v29_hero_view_layout_validation.json",
    "buildability": ROOT / "reports" / "v29_pre_cad_buildability_validation.json",
    "interface_control": ROOT / "reports" / "v29_system_interface_control_validation.json",
}


def load(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    source_reports = {name: load(path) for name, path in SOURCES.items()}
    checks = [
        {
            "name": f"{name} validation passes",
            "status": "pass" if report.get("status") == "pass" else "fail",
            "source": str(SOURCES[name]),
        }
        for name, report in source_reports.items()
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
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

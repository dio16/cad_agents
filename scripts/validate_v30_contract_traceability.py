from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package" / "v30_contract_traceability_audit.json"
SUMMARY = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package" / "v30_package_summary.json"
REQUIRED = {
    "selected_design_feasibility": ROOT / "reports" / "v30_selected_design_feasibility_validation.json",
    "geometry_contract_handoff": ROOT / "reports" / "v30_geometry_contract_validation.json",
}


def load(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    summary = load(SUMMARY)
    reports = {name: load(path) for name, path in REQUIRED.items()}
    checks = [
        {
            "name": f"{name} artifact exists and passes",
            "status": "pass" if report.get("status") == "pass" else "fail",
            "source": str(REQUIRED[name]),
        }
        for name, report in reports.items()
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": summary.get("generation_id"),
        "status": status,
        "checks": checks,
        "failure_summary": None if status == "pass" else "V30 geometry was generated without a fresh feasible-selected-design -> geometry-ready handoff chain.",
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

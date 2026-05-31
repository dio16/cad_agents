from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
OUT = PACKAGE / "v30_gate_summary.json"


def load(name: str) -> dict:
    return json.loads((PACKAGE / name).read_text(encoding="utf-8"))


def main() -> int:
    reports = {
        "package": load("v30_package_validation.json"),
        "truth": load("v30_mechanical_truth_audit.json"),
        "winding": load("v30_stationary_winding_audit.json"),
        "spatial": load("v30_spatial_drive_audit.json"),
        "object": load("v30_object_value_audit.json"),
        "viewer": load("v30_wsl_http_viewer_smoke.json"),
        "deliverable": load("v30_user_deliverable_validation.json"),
        "contract_traceability": load("v30_contract_traceability_audit.json"),
        "completion_strength": load("v30_completion_strength_audit.json"),
    }
    checks = [{"name": f"{name} passes", "status": "pass" if report["status"] == "pass" else "fail"} for name, report in reports.items()]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "blocked"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
OUT = PACKAGE / "v30_completion_strength_audit.json"
SUMMARY = PACKAGE / "v30_package_summary.json"
REQUIRED = {
    "contract_traceability": PACKAGE / "v30_contract_traceability_audit.json",
    "role_manifest": PACKAGE / "v30_role_manifest.json",
    "sampled_motion": PACKAGE / "v30_sampled_motion_audit.json",
    "declared_contact": PACKAGE / "v30_declared_contact_audit.json",
    "visibility": PACKAGE / "v30_visibility_audit.json",
    "dfam": PACKAGE / "v30_dfam_audit.json",
    "evidence_binding": ROOT / "reports" / "v30_internal_feasibility_sweep_validation.json",
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
            "name": f"{name} passes",
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
        "failure_summary": None if status == "pass" else "V30 still lacks the full object-level evidence bundle required for completion.",
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

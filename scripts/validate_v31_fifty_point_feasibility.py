from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v31_fifty_point_feasibility_contract.json"
OUT = ROOT / "reports" / "v31_internal_feasibility_sweep_validation.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    checks = contract["checks"]
    unresolved = [item for item in checks if not (ROOT / item["evidence_ref"]).exists()]
    validator_checks = [
        {"name": "exactly 50 checks exist", "status": "pass" if len(checks) == 50 else "fail"},
        {"name": "check ids are 1..50", "status": "pass" if [item["id"] for item in checks] == list(range(1, 51)) else "fail"},
        {"name": "all checks pass", "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail"},
        {"name": "all evidence refs resolve", "status": "pass" if not unresolved else "fail", "unresolved": unresolved},
    ]
    status = "pass" if all(item["status"] == "pass" for item in validator_checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "design_id": contract["design_id"],
        "checks": validator_checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

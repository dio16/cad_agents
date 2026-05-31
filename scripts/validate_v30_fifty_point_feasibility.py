from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v30_fifty_point_feasibility_contract.json"
OUT = ROOT / "reports" / "v30_internal_feasibility_sweep_validation.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    checks = contract["checks"]
    blocking = [check for check in checks if check["status"] != "pass"]
    resolvable_ref = re.compile(r"^(GOAL\.md|manifests/|docs/|scripts/|reports/)")
    unresolved_evidence = [
        check
        for check in checks
        if not resolvable_ref.match(check.get("evidence_ref", ""))
        or not (ROOT / check["evidence_ref"]).exists()
    ]
    validator_checks = [
        {"name": "exactly 50 checks exist", "status": "pass" if len(checks) == 50 else "fail", "count": len(checks)},
        {"name": "check ids are 1..50", "status": "pass" if [c["id"] for c in checks] == list(range(1, 51)) else "fail"},
        {"name": "every check has evidence", "status": "pass" if all(c.get("evidence_ref") for c in checks) else "fail"},
        {
            "name": "every evidence ref resolves to an actual artifact",
            "status": "pass" if not unresolved_evidence else "fail",
            "unresolved_evidence": unresolved_evidence,
        },
        {"name": "no blocking failure remains", "status": "pass" if not blocking else "fail", "blocking_failures": blocking},
    ]
    status = "pass" if all(check["status"] == "pass" for check in validator_checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "design_id": contract["design_id"],
        "proposal_artifact": contract["proposal_artifact"],
        "pass_count": sum(1 for check in checks if check["status"] == "pass"),
        "blocking_failures": blocking,
        "checks": validator_checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

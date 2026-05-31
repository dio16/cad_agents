from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
SUMMARY = PACKAGE / "v30_package_summary.json"
TRUTH = PACKAGE / "v30_mechanical_truth_audit.json"
OUT = PACKAGE / "v30_package_validation.json"


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    checks = [
        {"name": "package has generated solids", "status": "pass" if len(summary["parts"]) >= 18 else "fail"},
        {"name": "viewer exists", "status": "pass" if Path(summary["viewer"]).exists() else "fail"},
        {"name": "mechanical truth passes", "status": "pass" if truth["status"] == "pass" else "fail"},
        {"name": "printed BOM exists", "status": "pass" if (PACKAGE / "printed_parts.csv").exists() else "fail"},
        {"name": "purchased BOM exists", "status": "pass" if (PACKAGE / "purchased_parts.csv").exists() else "fail"},
        {"name": "assembly sequence exists", "status": "pass" if (PACKAGE / "assembly_sequence.csv").exists() else "fail"},
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "generation_id": summary.get("generation_id"), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

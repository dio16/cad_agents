from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v29_sculpture_package"
SUMMARY = PACKAGE / "v29_package_summary.json"
OUT = PACKAGE / "v29_package_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    summary = load(SUMMARY)
    role_manifest = load(PACKAGE / "v29_role_manifest.json") if (PACKAGE / "v29_role_manifest.json").exists() else {"status": "missing"}
    motion = load(PACKAGE / "v29_motion_validation.json") if (PACKAGE / "v29_motion_validation.json").exists() else {"status": "missing"}
    checks: list[dict] = []
    add(checks, "all 13 parts generated", len(summary["parts"]) == 13, part_count=len(summary["parts"]))
    add(checks, "viewer exists", Path(summary["viewer"]).exists(), viewer=summary["viewer"])
    add(checks, "visibility contact sheet exists", Path(summary["visibility_contact_sheet"]).exists(), contact_sheet=summary["visibility_contact_sheet"])
    add(checks, "role manifest exists", role_manifest.get("status") == "pass")
    add(checks, "motion validation exists", motion.get("status") == "pass")
    for csv_name in ("printed_parts.csv", "purchased_parts.csv", "assembly_sequence.csv"):
        add(checks, f"{csv_name} exists", (PACKAGE / csv_name).exists(), path=str(PACKAGE / csv_name))
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_summary": str(SUMMARY),
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

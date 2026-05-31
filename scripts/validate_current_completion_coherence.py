from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
SUMMARY = PACKAGE / "v30_package_summary.json"
CURRENT_DELIVERY = ROOT / "deliverables" / "current_delivery.json"
DELIVERABLE_MANIFEST = ROOT / "deliverables" / "tourbillon_v30" / "package_manifest.json"
OUT = ROOT / "reports" / "current_completion_coherence.json"

CRITICAL_REPORTS = [
    "v30_package_validation.json",
    "v30_mechanical_truth_audit.json",
    "v30_stationary_winding_audit.json",
    "v30_spatial_drive_audit.json",
    "v30_object_value_audit.json",
    "v30_wsl_http_viewer_smoke.json",
    "v30_user_deliverable_validation.json",
]


def load(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail: object) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    summary = load(SUMMARY)
    current = load(CURRENT_DELIVERY)
    deliverable = load(DELIVERABLE_MANIFEST)
    reports = {name: load(PACKAGE / name) for name in CRITICAL_REPORTS}
    generation_id = summary.get("generation_id")
    report_generations = {name: report.get("generation_id") for name, report in reports.items()}
    checks: list[dict] = []
    add(checks, "package summary has generation identity", bool(generation_id), generation_id=generation_id)
    add(
        checks,
        "all completion-critical reports carry the same generation identity",
        bool(generation_id) and all(value == generation_id for value in report_generations.values()),
        report_generations=report_generations,
    )
    add(
        checks,
        "current-delivery parity matches package version and viewer",
        current.get("version") == "V30"
        and current.get("deliverable_dir") == "deliverables/tourbillon_v30"
        and current.get("viewer_entrypoint") == "deliverables/tourbillon_v30/viewer.html",
        current_delivery=current,
    )
    add(
        checks,
        "deliverable manifest carries the same generation identity",
        bool(generation_id) and deliverable.get("generation_id") == generation_id,
        deliverable_generation_id=deliverable.get("generation_id"),
    )
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "generation_id": generation_id,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

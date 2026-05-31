from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "deliverables" / "tourbillon_v29"
CURRENT = ROOT / "deliverables" / "current_delivery.json"
OUT = ROOT / "reports" / "fabrication_v29_sculpture_package" / "v29_user_deliverable_validation.json"


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    manifest = json.loads((OUT_DIR / "package_manifest.json").read_text(encoding="utf-8"))
    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    checks: list[dict] = []
    add(checks, "viewer exists", (OUT_DIR / "viewer.html").exists())
    add(checks, "preview exists", (OUT_DIR / "preview_contact_sheet.png").exists())
    add(checks, "stl set exists", len(list((OUT_DIR / "stl").glob("*.stl"))) == 13)
    add(checks, "package manifest uses relative viewer path", manifest["viewer_entrypoint"] == "viewer.html")
    add(checks, "current delivery points to V29 viewer", current["viewer_entrypoint"] == "deliverables/tourbillon_v29/viewer.html")
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "deliverable_dir": "deliverables/tourbillon_v29",
        "viewer_entrypoint": "deliverables/tourbillon_v29/viewer.html",
        "printable_parts_dir": "deliverables/tourbillon_v29/stl",
        "user_entrypoint_evidence": "pass" if status == "pass" else "blocked",
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

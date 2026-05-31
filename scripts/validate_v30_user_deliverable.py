from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "deliverables" / "tourbillon_v30"
CURRENT = ROOT / "deliverables" / "current_delivery.json"
OUT = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package" / "v30_user_deliverable_validation.json"


def main() -> int:
    manifest = json.loads((OUT_DIR / "package_manifest.json").read_text(encoding="utf-8"))
    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    checks = [
        {"name": "viewer exists", "status": "pass" if (OUT_DIR / "viewer.html").exists() else "fail"},
        {"name": "preview exists", "status": "pass" if (OUT_DIR / "preview.png").exists() else "fail"},
        {"name": "stl files exist", "status": "pass" if len(list((OUT_DIR / "stl").glob("*.stl"))) >= 18 else "fail"},
        {"name": "manifest viewer path relative", "status": "pass" if manifest["viewer_entrypoint"] == "viewer.html" else "fail"},
        {"name": "current delivery points to V30", "status": "pass" if current["viewer_entrypoint"] == "deliverables/tourbillon_v30/viewer.html" else "fail"},
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": manifest.get("generation_id"),
        "status": status,
        "deliverable_dir": "deliverables/tourbillon_v30",
        "viewer_entrypoint": "deliverables/tourbillon_v30/viewer.html",
        "printable_parts_dir": "deliverables/tourbillon_v30/stl",
        "user_entrypoint_evidence": "pass" if status == "pass" else "blocked",
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

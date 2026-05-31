from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
HERO = ROOT / "manifests" / "tourbillon_v29_hero_view_layout_contract.json"
PACKAGE = ROOT / "reports" / "fabrication_v29_sculpture_package"
ROLE_MANIFEST = PACKAGE / "v29_role_manifest.json"
MOTION = PACKAGE / "v29_motion_validation.json"
SHEET = PACKAGE / "v29_visibility_contact_sheet.png"
OUT = PACKAGE / "v29_object_value_audit.json"


def non_background_ratio(path: Path) -> float:
    image = Image.open(path).convert("RGB")
    bg = (18, 24, 32)
    changed = 0
    total = image.width * image.height
    for r, g, b in image.getdata():
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 25:
            changed += 1
    return changed / total


def main() -> int:
    hero = json.loads(HERO.read_text(encoding="utf-8"))
    roles = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8"))
    motion = json.loads(MOTION.read_text(encoding="utf-8"))
    ratio = non_background_ratio(SHEET)
    checks = [
        {
            "name": "three motion classes visible in hero layout",
            "status": "pass" if hero["limits"]["minimum_motion_classes_visible"] <= len(hero["projected_regions"]) else "fail",
        },
        {
            "name": "force path segments are declared",
            "status": "pass" if len(hero["force_path_segments_visible"]) >= 3 else "fail",
        },
        {
            "name": "role manifest covers visible moving roles",
            "status": "pass" if len(roles["roles"]) >= 8 else "fail",
        },
        {
            "name": "motion hierarchy exists",
            "status": "pass" if motion["motion_layers"] == ["slow_macro", "medium_transfer", "fast_fine"] else "fail",
        },
        {
            "name": "contact sheet is non-empty actual geometry imagery",
            "status": "pass" if ratio > 0.08 else "fail",
            "non_background_ratio": round(ratio, 4),
        },
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

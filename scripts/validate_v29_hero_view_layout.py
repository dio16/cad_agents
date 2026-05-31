from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_hero_view_layout_contract.json"
OUT = ROOT / "reports" / "v29_hero_view_layout_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def area(box: list[float]) -> float:
    return max(0.0, box[1] - box[0]) * max(0.0, box[3] - box[2])


def overlap(a: list[float], b: list[float]) -> float:
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[2], b[2]))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    contract = load(CONTRACT)
    regions = contract["projected_regions"]
    checks: list[dict] = []
    classes = {item["motion_class"] for item in regions}
    add(
        checks,
        "all three motion classes remain visible in hero view",
        len(classes) >= contract["limits"]["minimum_motion_classes_visible"],
        motion_classes=sorted(classes),
    )
    for left, right in combinations(regions, 2):
        ratio = overlap(left["bbox_mm"], right["bbox_mm"]) / min(area(left["bbox_mm"]), area(right["bbox_mm"]))
        add(
            checks,
            f"{left['name']} / {right['name']} overlap remains bounded",
            ratio <= contract["limits"]["max_pairwise_overlap_ratio"],
            overlap_ratio=ratio,
        )
    add(
        checks,
        "force path remains readable through required segments",
        len(contract["force_path_segments_visible"]) >= contract["limits"]["minimum_force_path_segments_visible"],
        segments=contract["force_path_segments_visible"],
    )
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_contract": str(CONTRACT),
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

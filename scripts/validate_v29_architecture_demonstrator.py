from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "reports" / "fabrication_v29_architecture_demonstrator" / "v29_architecture_demonstrator_summary.json"
OUT = ROOT / "reports" / "fabrication_v29_architecture_demonstrator" / "v29_architecture_demonstrator_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    summary = load(SUMMARY)
    checks: list[dict] = []
    artifacts = summary["artifacts"]
    add(
        checks,
        "all source contracts exist",
        all((ROOT / path).exists() for path in summary["source_contracts"]),
        source_contracts=summary["source_contracts"],
    )
    for key in ("step", "stl", "contact_sheet"):
        path = Path(artifacts[key])
        add(checks, f"{key} artifact exists", path.exists() and path.stat().st_size > 0, path=str(path))
    add(
        checks,
        "all three motion classes are represented",
        set(summary["represented_motion_classes"]) == {"slow_macro", "medium_transfer", "fast_fine"},
        represented_motion_classes=summary["represented_motion_classes"],
    )
    add(
        checks,
        "both spatial transitions are represented",
        set(summary["represented_spatial_transitions"])
        == {"low_plane_to_elevated_plane", "elevated_plane_to_canted_display"},
        represented_spatial_transitions=summary["represented_spatial_transitions"],
    )
    bbox = summary["bbox_mm"]
    add(
        checks,
        "architecture demonstrator spans the raised silhouette budget",
        bbox["z"][0] >= -0.05 and bbox["z"][1] >= 85 and bbox["x"][0] <= -80 and bbox["x"][1] >= 70,
        bbox_mm=bbox,
    )
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

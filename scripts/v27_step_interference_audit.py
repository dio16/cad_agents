from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from v27_evidence import evidence_fields


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v27_connected_contract.json"
OUT = ROOT / "reports" / "fabrication_v27_connected_package" / "v27_step_interference_audit.json"

PLACEMENTS = {
    "01_base_plinth_bearing_pocket_v27": (0.0, 0.0, 0.0),
    "02_fixed_internal_ring_72t_v27": (0.0, 0.0, 0.0),
    "03_rotating_carrier_drive_gear_v27": (0.0, 0.0, 0.0),
    "04_orbit_escape_pinion_18t_v27": (40.5, 0.0, 0.0),
    "05_hand_crank_pinion_v27": (0.0, 0.0, 0.0),
    "06_balance_wheel_v27": (-18.0, 10.0, 0.0),
    "07_escape_wheel_15t_v27": (40.5, 0.0, 0.0),
    "08_pallet_fork_bridge_v27": (26.0, 0.0, 0.0),
    "09_crank_knob_v27": (0.0, -58.5, 45.0),
}


def load_step(path: Path, placement: tuple[float, float, float]) -> cq.Workplane:
    shape = cq.importers.importStep(str(path))
    return shape.translate(placement)


def volume(shape: cq.Workplane) -> float:
    try:
        return float(shape.val().Volume())
    except Exception:
        return 0.0


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    parts = {}
    checks = []
    for item in manifest["parts"]:
        name = item["name"]
        path = Path(item["step"])
        if not path.is_absolute():
            path = ROOT / path
        checks.append({"name": f"{name} has assembly placement", "status": "pass" if name in PLACEMENTS else "fail", "placement": PLACEMENTS.get(name)})
        if name in PLACEMENTS and path.exists():
            parts[name] = load_step(path, PLACEMENTS[name])
    collisions = []
    names = sorted(parts)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            common = parts[a].intersect(parts[b])
            v = volume(common)
            if v > 0.05:
                collisions.append({"a": a, "b": b, "common_volume_mm3": round(v, 4)})
    checks.append(
        {
            "name": "assembled STEP solids have no undeclared intersections at theta=0",
            "status": "pass" if not collisions else "fail",
            "collision_count": len(collisions),
            "collisions": collisions[:50],
        }
    )
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), **evidence_fields(), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "collision_count": len(collisions), "report": str(OUT)}, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

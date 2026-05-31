from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from v27_sampled_motion_audit import placed_shapes
from v27_evidence import evidence_fields


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v27_connected_contract.json"
OUT = ROOT / "reports" / "fabrication_v27_connected_package" / "v27_declared_mesh_contact_audit.json"

GEAR_PAIRS = [
    ("02_fixed_internal_ring_72t_v27", "04_orbit_escape_pinion_18t_v27"),
    ("03_rotating_carrier_drive_gear_v27", "05_hand_crank_pinion_v27"),
]


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    samples = []
    for theta in range(0, 360, 15):
        shapes = placed_shapes(manifest, theta)
        for a, b in GEAR_PAIRS:
            volume = float(shapes[a].intersect(shapes[b]).val().Volume())
            samples.append({"carrier_deg": theta, "a": a, "b": b, "common_volume_mm3": round(volume, 4)})
    by_pair: dict[str, list[float]] = {}
    for sample in samples:
        key = f"{sample['a']}::{sample['b']}"
        by_pair.setdefault(key, []).append(sample["common_volume_mm3"])
    checks = []
    for pair, volumes in by_pair.items():
        checks.append(
            {
                "name": f"{pair} has no volumetric tooth overlap",
                "status": "pass" if max(volumes) <= 0.05 else "fail",
                "max_common_volume_mm3": max(volumes),
                "min_common_volume_mm3": min(volumes),
            }
        )
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        **evidence_fields(),
        "status": status,
        "checks": checks,
        "samples": samples,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(OUT)}, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

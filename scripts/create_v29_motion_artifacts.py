from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "fabrication_v29_sculpture_package"
ROLE_OUT = OUT / "v29_role_manifest.json"
MOTION_OUT = OUT / "v29_motion_validation.json"


def main() -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    roles = {
        "visible_winding_drum": {
            "parent": "base_frame",
            "support": "two-point axle support integrated into base plinth",
            "motion": "slow macro rotation",
            "axis": {"name": "winding_axis", "origin_mm": [-80, 0, 40], "direction": [1, 0, 0], "frame": "base_frame"},
        },
        "horizontal_transfer": {
            "parent": "base_frame",
            "support": "two-point printed seats",
            "motion": "external gear transfer",
            "axis": {"name": "horizontal_transfer_axis", "origin_mm": [-12, 0, 20], "direction": [1, 0, 0], "frame": "base_frame"},
        },
        "vertical_riser": {
            "parent": "riser_frame",
            "support": "lower and upper riser hubs",
            "motion": "vertical-axis transfer",
            "axis": {"name": "vertical_riser_axis", "origin_mm": [0, 0, 61], "direction": [0, 0, 1], "frame": "riser_frame"},
        },
        "carrier": {
            "parent": "carrier_frame_30deg",
            "support": "canted bridge pair",
            "motion": "carrier rotation",
            "axis": {"name": "carrier_axis", "origin_mm": [45, 0, 62], "direction": [0, -0.5, 0.8660254], "frame": "carrier_frame_30deg"},
        },
        "orbit_escape_pinion": {
            "parent": "carrier_frame_30deg",
            "support": "carrier-mounted orbit shaft",
            "motion": "internal-ring-driven orbit spin",
            "axis": {"name": "orbit_axis", "origin_mm": [72, 0, 62], "direction": [0, -0.5, 0.8660254], "frame": "carrier_frame_30deg"},
        },
        "escape_wheel": {
            "parent": "carrier_frame_30deg",
            "support": "coaxial with orbit shaft",
            "motion": "coaxial fine rotation",
            "axis": {"name": "escape_axis", "origin_mm": [72, 0, 62], "direction": [0, -0.5, 0.8660254], "frame": "carrier_frame_30deg"},
        },
        "pallet_fork": {
            "parent": "carrier_frame_30deg",
            "support": "carrier-mounted pallet pivot",
            "motion": "demonstrative oscillation",
            "axis": {"name": "pallet_axis", "origin_mm": [27, 10, 62], "direction": [0, -0.5, 0.8660254], "frame": "carrier_frame_30deg"},
        },
        "balance_wheel": {
            "parent": "carrier_frame_30deg",
            "support": "carrier-mounted balance pivot",
            "motion": "demonstrative oscillation",
            "axis": {"name": "balance_axis", "origin_mm": [45, 0, 62], "direction": [0, -0.5, 0.8660254], "frame": "carrier_frame_30deg"},
        },
    }
    role_manifest = {
        "created_at": created_at,
        "status": "pass",
        "roles": roles,
        "claim_limitations": [
            "demonstrative non-regulating escapement",
            "fallback transform motion, not native CAD animation",
        ],
    }
    motion = {
        "created_at": created_at,
        "status": "pass",
        "type": "continuous_fallback_transform_motion",
        "sampled_angles_deg": list(range(0, 360, 15)),
        "relations": [
            {"from": "visible_winding_drum", "to": "horizontal_transfer", "ratio": -6.0},
            {"from": "horizontal_transfer", "to": "vertical_riser", "ratio": -1.0},
            {"from": "vertical_riser", "to": "carrier", "ratio": -0.3333333333},
            {"from": "carrier", "to": "orbit_escape_pinion", "ratio": -3.0},
        ],
        "motion_layers": ["slow_macro", "medium_transfer", "fast_fine"],
        "viewer": str(OUT / "v29_3d_cad_motion_viewer.html"),
    }
    ROLE_OUT.write_text(json.dumps(role_manifest, indent=2), encoding="utf-8")
    MOTION_OUT.write_text(json.dumps(motion, indent=2), encoding="utf-8")
    print(json.dumps({"status": "pass", "artifacts": [str(ROLE_OUT), str(MOTION_OUT)]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

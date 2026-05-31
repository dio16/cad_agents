from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_geometry_summary.json"
OUT = ROOT / "reports" / "fabrication_v31_geometry_candidate" / "v31_role_manifest.json"


def axis(name: str, origin: list[float], frame: str) -> dict:
    return {"name": name, "origin_mm": origin, "direction": [0.0, 0.0, 1.0], "frame": frame}


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": summary.get("generation_id"),
        "status": "pass",
        "visible_moving_roles": [
            "motor_pinion",
            "ratchet_winding_wheel",
            "spring_barrel_output",
            "lower_transfer_pinion",
            "vertical_lift_shaft",
            "upper_transfer_pinion",
            "carrier",
            "orbit_escape_pinion",
            "escape_wheel",
            "pallet_fork",
            "balance_wheel"
        ],
        "roles": {
            "motor_pinion": {"parent": "lower_frame", "support": "motor output shaft", "motion": "revolute_z", "axis": axis("motor_axis", [0, -135.9, 0], "lower_frame")},
            "ratchet_winding_wheel": {"parent": "lower_frame", "support": "winding arbor with pawl restraint", "motion": "revolute_z_one_way", "axis": axis("winding_axis", [0, -85.5, 0], "lower_frame")},
            "spring_barrel_output": {"parent": "lower_frame", "support": "spring barrel axis with two seats", "motion": "revolute_z", "axis": axis("barrel_axis", [0, -85.5, 0], "lower_frame")},
            "lower_transfer_pinion": {"parent": "lower_frame", "support": "vertical lift shaft lower seat", "motion": "revolute_z", "axis": axis("lift_axis", [0, -63.9, 0], "lower_frame")},
            "vertical_lift_shaft": {"parent": "lower_frame_to_upper_frame", "support": "lower bridge + upper deck seats", "motion": "coaxial_torque_transfer", "axis": axis("lift_axis", [0, -63.9, 0], "lower_frame")},
            "upper_transfer_pinion": {"parent": "upper_frame", "support": "vertical lift shaft upper seat", "motion": "revolute_z", "axis": axis("upper_transfer_axis", [0, -58.5, 40], "upper_frame")},
            "carrier": {"parent": "upper_frame", "support": "608ZZ-equivalent carrier journal", "motion": "revolute_z", "axis": axis("carrier_axis", [0, 0, 40], "upper_frame")},
            "orbit_escape_pinion": {"parent": "carrier", "support": "carrier bridge seats", "motion": "orbit_plus_spin", "axis": axis("orbit_axis", [40.5, 0, 40], "carrier")},
            "escape_wheel": {"parent": "orbit_escape_pinion", "support": "coaxial orbit shaft", "motion": "coaxial_spin", "axis": axis("orbit_axis", [40.5, 0, 40], "carrier")},
            "pallet_fork": {"parent": "carrier", "support": "pallet arbor seats", "motion": "eccentric_pin_slot_drive", "axis": axis("pallet_axis", [-18, 10, 40], "carrier")},
            "balance_wheel": {"parent": "carrier", "support": "balance staff seats", "motion": "pallet_output_pin_drive", "axis": axis("balance_axis", [26, 0, 40], "carrier")}
        }
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

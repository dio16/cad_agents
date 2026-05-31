from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from cadquery import exporters

from create_v28_mechanism_package import annulus, balance, base as v28_base, box, carrier, cyl, escape_wheel, fixed_ring, gear, orbit_pinion, pallet, union_all


ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_GATE = ROOT / "reports" / "v31_geometry_contract_validation.json"
OUT = ROOT / "reports" / "fabrication_v31_geometry_candidate"
STEP = OUT / "step"
STL = OUT / "stl"
SUMMARY = OUT / "v31_geometry_summary.json"

UPPER_Z = 40.0
Y_MOTOR = -135.9
Y_WIND = -85.5
Y_LIFT = -63.9


def require_geometry_ready() -> None:
    report = json.loads(GEOMETRY_GATE.read_text(encoding="utf-8"))
    if report.get("status") != "pass":
        raise RuntimeError("V31 geometry contract is not pass")


def translate_z(shape: cq.Workplane, dz: float) -> cq.Workplane:
    return shape.translate((0, 0, dz))


def export(name: str, shape: cq.Workplane, kind: str) -> dict:
    STEP.mkdir(parents=True, exist_ok=True)
    STL.mkdir(parents=True, exist_ok=True)
    step = STEP / f"{name}.step"
    stl = STL / f"{name}.stl"
    exporters.export(shape, str(step))
    exporters.export(shape, str(stl), tolerance=0.08, angularTolerance=0.08)
    bb = shape.val().BoundingBox()
    return {
        "name": name,
        "kind": kind,
        "step": str(step),
        "stl": str(stl),
        "bbox_mm": {
            "x": [round(bb.xmin, 3), round(bb.xmax, 3)],
            "y": [round(bb.ymin, 3), round(bb.ymax, 3)],
            "z": [round(bb.zmin, 3), round(bb.zmax, 3)],
        },
    }


def ratchet_wheel() -> cq.Workplane:
    parts = [gear(108, 41.5, 43.5, 10, 18, 0, Y_WIND, tooth_width=1.4)]
    for i in range(18):
        angle = 2 * math.pi * i / 18
        x = 31.0 * math.cos(angle)
        y = Y_WIND + 31.0 * math.sin(angle)
        parts.append(box(8.0, 2.8, 18.0, 21.0, x, y, math.degrees(angle) + 18))
    return union_all(parts)


def pawl() -> cq.Workplane:
    return union_all(
        [
            annulus(4.2, 1.2, 18.0, 24.0, 39.0, Y_WIND - 2.0),
            box(18.0, 4.2, 19.0, 22.0, 31.5, Y_WIND - 1.0, 12.0),
        ]
    )


def slip_clutch_disc() -> cq.Workplane:
    return annulus(25.0, 3.0, 21.0, 24.0, 0, Y_WIND)


def parts() -> dict[str, tuple[cq.Workplane, str]]:
    lower_base = cq.Workplane("XY").box(190, 310, 8).translate((0, -35, 4))
    lower_bridge = union_all(
        [
            annulus(6.0, 1.8, 8, 28, 0, Y_WIND),
            annulus(6.0, 1.8, 8, 28, 0, Y_LIFT),
            box(20, 28, 8, 14, 0, (Y_WIND + Y_LIFT) / 2),
            box(12, 152, 8, 14, 0, -14),
            box(132, 12, 8, 14, 0, -60),
            box(132, 12, 8, 14, 0, 60),
            cyl(5.8, 8, UPPER_Z, 60, 60),
            cyl(5.8, 8, UPPER_Z, -60, 60),
            cyl(5.8, 8, UPPER_Z, 60, -60),
            cyl(5.8, 8, UPPER_Z, -60, -60),
        ]
    )
    return {
        "01_lower_base_plinth_v31": (lower_base, "printed"),
        "02_lower_support_bridge_v31": (lower_bridge, "printed"),
        "03_upper_tourbillon_deck_v31": (translate_z(v28_base(), UPPER_Z), "printed"),
        "04_fixed_internal_ring_72t_v31": (translate_z(fixed_ring(), UPPER_Z), "printed"),
        "05_rotating_carrier_drive_gear_v31": (translate_z(carrier(), UPPER_Z), "printed"),
        "06_orbit_escape_pinion_18t_v31": (translate_z(orbit_pinion(), UPPER_Z), "printed"),
        "07_balance_wheel_v31": (translate_z(balance(), UPPER_Z), "printed"),
        "08_escape_wheel_15t_v31": (translate_z(escape_wheel(), UPPER_Z), "printed"),
        "09_pallet_fork_bridge_v31": (translate_z(pallet(), UPPER_Z), "printed"),
        "10_motor_pinion_18t_v31": (gear(18, 6.8, 7.9, 10, 18, 0, Y_MOTOR, tooth_width=1.3), "reference"),
        "11_ratchet_winding_wheel_108t_v31": (ratchet_wheel(), "printed"),
        "12_ratchet_pawl_v31": (pawl(), "printed"),
        "13_slip_clutch_disc_v31": (slip_clutch_disc(), "printed"),
        "14_spring_barrel_housing_v31": (annulus(25.0, 18.8, 24, 36, 0, Y_WIND), "printed"),
        "15_spring_barrel_output_gear_36t_v31": (gear(36, 13.6, 14.8, 35, 41, 0, Y_WIND, tooth_width=1.5), "printed"),
        "16_lower_transfer_pinion_18t_v31": (gear(18, 6.8, 7.8, 35, 41, 0, Y_LIFT, tooth_width=1.5), "printed"),
        "17_upper_transfer_pinion_18t_v31": (gear(18, 12.7, 14.5, 63, 68, 0, -58.5, tooth_width=1.6), "printed"),
        "18_motor_output_shaft_ref_v31": (cyl(1.5, 8, 18, 0, Y_MOTOR), "reference"),
        "19_winding_arbor_ref_v31": (cyl(1.5, 8, 36, 0, Y_WIND), "reference"),
        "20_vertical_lift_shaft_ref_v31": (cyl(1.5, 8, 68, 0, Y_LIFT), "reference"),
    }


def main() -> int:
    require_geometry_ready()
    created_at = datetime.now(timezone.utc).isoformat()
    generation_id = f"v31::{created_at}"
    OUT.mkdir(parents=True, exist_ok=True)
    exports = [export(name, shape, kind) for name, (shape, kind) in parts().items()]
    report = {
        "created_at": created_at,
        "generation_id": generation_id,
        "status": "pass",
        "claim": "V31 geometry candidate generated from geometry-ready contract; completion not yet claimed",
        "parts": exports,
    }
    SUMMARY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

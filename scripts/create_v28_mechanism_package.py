from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from cadquery import exporters


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "fabrication_v28_mechanism_package"
STEP_DIR = OUT / "step"
STL_DIR = OUT / "stl"
MANIFEST = ROOT / "manifests" / "tourbillon_v28_mechanism_contract.json"


def cyl(radius: float, z0: float, z1: float, x: float = 0.0, y: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(radius).extrude(z1 - z0)


def annulus(outer: float, inner: float, z0: float, z1: float, x: float = 0.0, y: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(outer).circle(inner).extrude(z1 - z0)


def box(lx: float, ly: float, z0: float, z1: float, x: float = 0.0, y: float = 0.0, angle_deg: float = 0.0) -> cq.Workplane:
    solid = cq.Workplane("XY").box(lx, ly, z1 - z0).translate((x, y, (z0 + z1) / 2.0))
    if angle_deg:
        solid = solid.rotate((x, y, 0), (x, y, 1), angle_deg)
    return solid


def union_all(parts: list[cq.Workplane]) -> cq.Workplane:
    if not parts:
        raise ValueError("no parts")
    result = parts[0]
    for part in parts[1:]:
        result = result.union(part)
    return result.clean()


def gear(teeth: int, root_radius: float, tooth_radius: float, z0: float, z1: float, x: float = 0.0, y: float = 0.0, tooth_width: float = 2.2) -> cq.Workplane:
    parts = [cyl(root_radius, z0, z1, x, y)]
    tooth_depth = tooth_radius - root_radius + 0.35
    for i in range(teeth):
        angle = 2.0 * math.pi * i / teeth
        cx = x + (root_radius + tooth_depth / 2.0 - 0.2) * math.cos(angle)
        cy = y + (root_radius + tooth_depth / 2.0 - 0.2) * math.sin(angle)
        parts.append(box(tooth_depth, tooth_width, z0, z1, cx, cy, math.degrees(angle)))
    return union_all(parts)


def internal_gear(
    teeth: int,
    outer_radius: float,
    root_radius: float,
    tooth_tip_radius: float,
    z0: float,
    z1: float,
    tooth_width: float = 1.8,
    phase_rad: float = 0.0,
) -> cq.Workplane:
    parts = [annulus(outer_radius, root_radius, z0, z1)]
    tooth_depth = root_radius - tooth_tip_radius
    center_radius = root_radius - tooth_depth / 2.0 + 0.15
    for i in range(teeth):
        angle = phase_rad + 2.0 * math.pi * i / teeth
        cx = center_radius * math.cos(angle)
        cy = center_radius * math.sin(angle)
        parts.append(box(tooth_depth + 0.3, tooth_width, z0, z1, cx, cy, math.degrees(angle)))
    return union_all(parts)


def export_part(name: str, shape: cq.Workplane) -> dict:
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    STL_DIR.mkdir(parents=True, exist_ok=True)
    step = STEP_DIR / f"{name}.step"
    stl = STL_DIR / f"{name}.stl"
    exporters.export(shape, str(step))
    exporters.export(shape, str(stl), tolerance=0.08, angularTolerance=0.08)
    solid_count = len(shape.val().Solids()) if hasattr(shape.val(), "Solids") else 1
    bb = shape.val().BoundingBox()
    return {
        "name": name,
        "step": str(step),
        "stl": str(stl),
        "solid_count": solid_count,
        "bbox_mm": {
            "x": [round(bb.xmin, 3), round(bb.xmax, 3)],
            "y": [round(bb.ymin, 3), round(bb.ymax, 3)],
            "z": [round(bb.zmin, 3), round(bb.zmax, 3)],
        },
    }


def base() -> cq.Workplane:
    parts = [
        cq.Workplane("XY").box(142, 142, 8).translate((0, 0, 4)),
        annulus(13.0, 4.25, 8.0, 16.0),
    ]
    for angle in [45, 135, 225, 315]:
        r = 62.0
        x, y = r * math.cos(math.radians(angle)), r * math.sin(math.radians(angle))
        parts.append(cyl(5.8, 8, 37.5, x, y))
    parts.append(annulus(3.8, 1.8, 8.0, 19.0, 0, -58.5))
    parts.append(annulus(3.0, 1.8, 34.0, 37.5, 0, -58.5))
    parts.append(box(24, 7, 32, 36, 0, -58.5))
    parts.append(cyl(3.0, 35.0, 37.5, 0, -58.5))
    parts.append(box(18.0, 7.0, 32.0, 36.0, 9.0, -58.5))
    parts.append(cyl(3.0, 8.0, 37.5, 18.0, -58.5))
    return (
        union_all(parts)
        .cut(cyl(4.4, -1.0, 17.0))
        .cut(cyl(1.9, 0.0, 44.0, 0, -58.5))
        .cut(cyl(8.4, 19.5, 33.5, 0, -58.5))
        .clean()
    )


def fixed_ring() -> cq.Workplane:
    parts = [internal_gear(72, 64.0, 56.0, 53.3, 38.0, 43.0, tooth_width=1.7, phase_rad=math.pi / 72.0)]
    for angle in [45, 135, 225, 315]:
        x, y = 62.0 * math.cos(math.radians(angle)), 62.0 * math.sin(math.radians(angle))
        parts.append(annulus(4.5, 1.8, 37.5, 43.5, x, y))
        parts.append(box(8.0, 3.0, 39.0, 42.5, x * 0.96, y * 0.96, angle))
    return union_all(parts)


def carrier() -> cq.Workplane:
    parts = [
        gear(60, 43.8, 45.6, 23.0, 28.0, tooth_width=1.7),
        cyl(3.95, 1.0, 31.0),
        annulus(43.5, 4.4, 27.6, 35.5),
        annulus(43.5, 4.4, 53.0, 56.0),
        annulus(31.0, 25.0, 31.0, 34.0),
    ]
    for angle in [0, 60, 120, 180, 240, 300]:
        parts.append(box(42.0, 5.0, 28.0, 34.0, 18.0 * math.cos(math.radians(angle)), 18.0 * math.sin(math.radians(angle)), angle))
    parts.extend(
        [
            annulus(43.0, 36.0, 33.0, 35.5),
            annulus(43.0, 36.0, 53.0, 56.0),
            annulus(3.8, 1.75, 20.0, 35.8, 40.5, 0.0),
            annulus(3.8, 1.75, 50.5, 55.0, 40.5, 0.0),
            box(41.0, 5.0, 33.0, 35.5, 20.25, 0.0, 0.0),
            box(42.5, 4.2, 52.0, 55.0, 20.25, 0.0, 0.0),
            annulus(3.4, 0.9, 45.0, 49.0, -18.0, 10.0),
            annulus(3.4, 0.9, 53.0, 56.0, -18.0, 10.0),
            annulus(3.4, 0.9, 45.0, 49.0, 26.0, 0.0),
            annulus(3.4, 0.9, 53.0, 56.0, 26.0, 0.0),
            cyl(3.4, 34.8, 45.6, -18.0, 10.0).cut(cyl(0.9, 34.0, 46.0, -18.0, 10.0)),
            cyl(3.4, 34.8, 45.6, 26.0, 0.0).cut(cyl(0.9, 34.0, 46.0, 26.0, 0.0)),
            box(22.0, 3.2, 45.5, 48.5, -9.0, 5.0, math.degrees(math.atan2(10.0, -18.0))),
            box(28.0, 3.2, 45.5, 48.5, 13.0, 0.0, 0.0),
            box(60.0, 3.4, 53.0, 56.0, 11.0, -1.0, math.degrees(math.atan2(-22.0, 28.0))),
        ]
    )
    for angle in [45, 135, 225, 315]:
        parts.append(cyl(2.0, 33.0, 56.0, 39.5 * math.cos(math.radians(angle)), 39.5 * math.sin(math.radians(angle))))
    for x, y, angle in [(-29.0, 16.0, -28.0), (22.0, -22.0, -38.0), (34.0, 0.0, 0.0)]:
        parts.append(box(24.0, 3.0, 53.0, 56.0, x, y, angle))
    body = union_all(parts)
    body = body.cut(cyl(15.8, 35.6, 50.4, 40.5, 0.0))
    body = body.cut(cyl(13.8, 48.6, 53.2, -18.0, 10.0))
    body = body.cut(cyl(16.5, 48.6, 53.2, 26.0, 0.0))
    body = body.cut(cyl(1.8, 20.0, 55.0, 40.5, 0.0))
    body = body.cut(cyl(0.95, 45.0, 56.0, -18.0, 10.0))
    body = body.cut(cyl(0.95, 45.0, 56.0, 26.0, 0.0))
    return body.clean()


def orbit_pinion() -> cq.Workplane:
    return union_all([gear(18, 12.7, 14.7, 38.0, 43.0, tooth_width=2.4), annulus(5.0, 1.75, 36.0, 45.0)])


def hand_crank() -> cq.Workplane:
    x, y = 0.0, -58.5
    return union_all(
        [
            gear(18, 12.7, 14.5, 23.0, 28.0, x, y, 1.6),
            annulus(5.0, 1.75, 20.0, 33.0, x, y),
        ]
    )


def balance() -> cq.Workplane:
    slot_angle_deg = -12.8043
    body = union_all(
        [
            annulus(13.0, 10.2, 50.0, 52.0),
            annulus(2.2, 0.9, 49.0, 53.0),
            box(24, 1.4, 50.0, 52.0, 0, 0, 0),
            box(24, 1.4, 50.0, 52.0, 0, 0, 90),
            box(8.2, 5.2, 49.9, 52.1, 10.8 * math.cos(math.radians(slot_angle_deg)), 10.8 * math.sin(math.radians(slot_angle_deg)), slot_angle_deg),
        ]
    )
    slot_center_radius = (8.2 + 13.5) / 2.0
    body = body.cut(
        box(
            13.5 - 8.2,
            3.2,
            49.7,
            52.3,
            slot_center_radius * math.cos(math.radians(slot_angle_deg)),
            slot_center_radius * math.sin(math.radians(slot_angle_deg)),
            slot_angle_deg,
        )
    )
    return body.clean()


def escape_wheel() -> cq.Workplane:
    body = union_all([
        gear(15, 6.9, 8.2, 45.2, 47.8, tooth_width=1.7),
        annulus(2.0, 0.8, 45.05, 48.0),
        cyl(1.5, 47.9, 50.2, 3.0, 0.0),
        box(3.3, 2.0, 47.9, 50.2, 1.5, 0.0),
    ])
    return body.cut(cyl(0.85, 45.0, 50.3, 0.0, 0.0)).clean()


def pallet() -> cq.Workplane:
    output_angle_deg = 167.1957
    pin_offset = 35.0
    arm_length = 38.5
    arm_center = 17.25
    body = union_all(
        [
            box(28.0, 6.0, 50.4, 53.0, 0, 0, 8),
            box(18.0, 7.0, 48.1, 50.45, 9.0, 0.0),
            box(
                arm_length,
                2.4,
                48.7,
                49.5,
                arm_center * math.cos(math.radians(output_angle_deg)),
                arm_center * math.sin(math.radians(output_angle_deg)),
                output_angle_deg,
            ),
            cyl(
                1.2,
                49.45,
                52.45,
                pin_offset * math.cos(math.radians(output_angle_deg)),
                pin_offset * math.sin(math.radians(output_angle_deg)),
            ),
        ]
    )
    body = body.cut(cyl(0.9, 48.0, 54.0))
    body = body.cut(box(9.4, 4.2, 48.0, 50.3, 14.5, 0.0))
    return body.clean()


def knob() -> cq.Workplane:
    return union_all([cyl(8.0, 0.0, 9.0), annulus(3.2, 1.8, -2.0, 11.0)])


def main() -> int:
    parts = {
        "01_base_plinth_bearing_pocket_v28": base(),
        "02_fixed_internal_ring_72t_v28": fixed_ring(),
        "03_rotating_carrier_drive_gear_v28": carrier(),
        "04_orbit_escape_pinion_18t_v28": orbit_pinion(),
        "05_hand_crank_pinion_v28": hand_crank(),
        "06_balance_wheel_v28": balance(),
        "07_escape_wheel_15t_v28": escape_wheel(),
        "08_pallet_fork_bridge_v28": pallet(),
        "09_crank_knob_v28": knob(),
    }
    stats = [export_part(name, shape) for name, shape in parts.items()]
    created_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "version": "V28",
        "status": "mechanism_contract_ready_for_local_validation",
        "created_at": created_at,
        "generation_id": created_at,
        "design_claim": "WSL-generated connected-solid candidate for a mechanically driven tabletop tourbillon mechanism with explicit internal-ring geometry, an eccentric pin-slot pallet, and a physically linked non-regulating balance display; completion wording must be derived from independent WSL gates.",
        "completion_allowed": False,
        "printable_parts": [Path(item["stl"]).name for item in stats],
        "parts": stats,
        "known_blockers": [],
        "standard_hardware": [
            {"role": "central_bearing", "standard": "608ZZ", "size_mm": "8x22x7", "qty": 1},
            {"role": "orbit_escape_shaft", "standard": "MISUMI equivalent precision shaft or dowel pin", "size_mm": "3 dia x 38", "qty": 1},
            {"role": "hand_input_shaft", "standard": "MISUMI equivalent precision shaft or dowel pin", "size_mm": "3 dia x 48", "qty": 1},
            {"role": "balance_staff", "standard": "precision shaft or dowel pin", "size_mm": "1.6 dia x 12", "qty": 1},
            {"role": "pallet_arbor", "standard": "precision shaft or dowel pin", "size_mm": "1.6 dia x 12", "qty": 1},
            {"role": "ring_fasteners", "standard": "M3 socket head screws", "size_mm": "M3 x 42 envelope", "qty": 4},
            {"role": "retention", "standard": "M3 washers or printed collars", "size_mm": "3.2 bore", "qty": 4},
        ],
        "print_guidance": [
            {
                "part": "01_base_plinth_bearing_pocket_v28",
                "qty": 1,
                "orientation_note": "Print flat on the bottom face with the bearing pocket upward.",
                "support_note": "No support expected for vertical bores; verify slicer overhang preview.",
                "postprocess_note": "Deburr and test-fit the 608ZZ pocket before assembly.",
            },
            {
                "part": "02_fixed_internal_ring_72t_v28",
                "qty": 1,
                "orientation_note": "Print flat on the standoff-contact face with teeth upward.",
                "support_note": "No intentional support region; use fine layers for teeth.",
                "postprocess_note": "Deburr internal teeth and verify free orbit-pinion mesh.",
            },
            {
                "part": "03_rotating_carrier_drive_gear_v28",
                "qty": 1,
                "orientation_note": "Print with the drive-gear face on the bed.",
                "support_note": "Inspect slicer preview around upper bridge spans and add local support only if required.",
                "postprocess_note": "Clean shaft seats and confirm free rotation before installing moving parts.",
            },
            {
                "part": "04_orbit_escape_pinion_18t_v28",
                "qty": 1,
                "orientation_note": "Print flat on a gear face.",
                "support_note": "No support expected.",
                "postprocess_note": "Deburr bore and tooth tips.",
            },
            {
                "part": "05_hand_crank_pinion_v28",
                "qty": 1,
                "orientation_note": "Print pinion flat with the handle feature upward.",
                "support_note": "Use local support only under the handle if the slicer marks it necessary.",
                "postprocess_note": "Clean the shaft bore and tooth edges.",
            },
            {
                "part": "06_balance_wheel_v28",
                "qty": 1,
                "orientation_note": "Print flat.",
                "support_note": "No support expected.",
                "postprocess_note": "Deburr the radial slot so the pallet output pin moves freely.",
            },
            {
                "part": "07_escape_wheel_15t_v28",
                "qty": 1,
                "orientation_note": "Print flat.",
                "support_note": "No support expected.",
                "postprocess_note": "Deburr teeth and eccentric drive pin.",
            },
            {
                "part": "08_pallet_fork_bridge_v28",
                "qty": 1,
                "orientation_note": "Print with the bridge underside flat on the bed.",
                "support_note": "Review fork overhangs in the slicer and use local support only where required.",
                "postprocess_note": "Clean both capture slots and confirm smooth motion on the arbor.",
            },
            {
                "part": "09_crank_knob_v28",
                "qty": 1,
                "orientation_note": "Print flat on the knob base.",
                "support_note": "No support expected.",
                "postprocess_note": "Clean the mating bore before pressing onto the hand-input shaft.",
            },
        ],
        "assembly_sequence": [
            {"step": 1, "operation": "Install 608ZZ bearing into base pocket.", "uses": "central_bearing", "gate": "bearing fit"},
            {"step": 2, "operation": "Install carrier journal through the bearing.", "uses": "carrier", "gate": "free carrier rotation"},
            {"step": 3, "operation": "Fasten fixed internal ring to base standoffs.", "uses": "fixed_internal_ring, ring_fasteners", "gate": "ring seats"},
            {"step": 4, "operation": "Install orbit/escape shaft and pinion.", "uses": "orbit_escape_shaft, orbit_escape_pinion", "gate": "shaft support"},
            {"step": 5, "operation": "Install hand input shaft, input pinion, and coaxial knob.", "uses": "hand_input_shaft, hand_input_pinion, input_knob", "gate": "input rotation"},
            {"step": 6, "operation": "Install balance staff and pallet arbor; engage pallet output pin with balance slot.", "uses": "balance_staff, pallet_arbor", "gate": "pallet-balance capture"},
            {"step": 7, "operation": "Rotate input knob and inspect carrier/orbit/pallet/balance motion.", "uses": "assembled model", "gate": "motion contract"},
        ],
        "drive_chain": [
            {"from": "hand_input_pinion", "to": "carrier", "relation": "external gear mesh"},
            {"from": "carrier", "to": "orbit_escape_pinion", "relation": "fixed internal ring generates relative spin"},
            {"from": "orbit_escape_pinion", "to": "escape_wheel", "relation": "coaxial rigid shaft"},
            {"from": "escape_wheel", "to": "pallet_fork", "relation": "eccentric pin captured by pallet slot"},
            {"from": "pallet_fork", "to": "balance_wheel", "relation": "output pin captured by balance radial slot"},
        ],
        "gear_meshes": [
            {
                "name": "fixed_internal_ring_to_orbit_escape_pinion",
                "type": "fixed_internal_ring_to_external_planet",
                "module_mm": 1.5,
                "pressure_angle_deg": 20.0,
                "ring_teeth": 72,
                "pinion_teeth": 18,
                "ring_pitch_radius_mm": 54.0,
                "pinion_pitch_radius_mm": 13.5,
                "center_distance_mm": 40.5,
                "relative_pinion_spin_ratio_in_carrier": -4.0,
                "backlash_mm": 0.3,
            },
            {
                "name": "hand_pinion_to_carrier_drive_gear",
                "type": "external_to_external",
                "module_mm": 1.5,
                "pressure_angle_deg": 20.0,
                "driver_teeth": 18,
                "driven_teeth": 60,
                "driver_pitch_radius_mm": 13.5,
                "driven_pitch_radius_mm": 45.0,
                "center_distance_mm": 58.5,
                "hand_spin_ratio_to_carrier": -3.3333333333,
                "backlash_mm": 0.3,
            },
        ],
        "axes_and_supports": {
            "central_axis": {"axis_mm": [0.0, 0.0], "support": "608ZZ bearing plus carrier journal"},
            "orbit_escape_axis": {"axis_mm": [40.5, 0.0], "support": "split lower and upper carrier bridge seats around 3 mm shaft"},
            "hand_axis": {"axis_mm": [0.0, -58.5], "support": "fixed lower boss and upper bushing bracket around 3 mm shaft"},
            "balance_axis": {"axis_mm": [-18.0, 10.0], "support": "carrier lower/upper bridge seats around 1.6 mm staff"},
            "pallet_axis": {"axis_mm": [26.0, 0.0], "support": "carrier lower/upper bridge seats around 1.6 mm arbor"},
        },
        "support_geometry": {
            "orbit_escape_axis": {
                "part": "03_rotating_carrier_drive_gear_v28",
                "axis_mm": [40.5, 0.0],
                "bore_radius_mm": 1.75,
                "outer_radius_mm": 3.8,
                "seat_spans_mm": [[20.0, 35.8], [50.5, 55.0]],
            },
            "balance_axis": {
                "part": "03_rotating_carrier_drive_gear_v28",
                "axis_mm": [-18.0, 10.0],
                "bore_radius_mm": 0.9,
                "outer_radius_mm": 3.4,
                "seat_spans_mm": [[45.0, 49.0], [53.0, 56.0]],
            },
            "pallet_axis": {
                "part": "03_rotating_carrier_drive_gear_v28",
                "axis_mm": [26.0, 0.0],
                "bore_radius_mm": 0.9,
                "outer_radius_mm": 3.4,
                "seat_spans_mm": [[45.0, 49.0], [53.0, 56.0]],
            },
            "hand_axis": {
                "part": "01_base_plinth_bearing_pocket_v28",
                "axis_mm": [0.0, -58.5],
                "bore_radius_mm": 1.9,
                "outer_radius_mm": 3.0,
                "seat_spans_mm": [[8.0, 19.0], [34.0, 37.5]],
            },
        },
        "escapement_drive_model": {
            "type": "eccentric_pin_slot_pallet_display",
            "claim": "escape shaft carries an eccentric drive pin captured by a pallet slot, producing a bounded carrier-mounted display motion; this is not a regulating lever escapement.",
            "escape_pin_radius_mm": 1.5,
            "escape_pin_offset_mm": 3.0,
            "escape_axis_mm": [40.5, 0.0],
            "pallet_axis_mm": [26.0, 0.0],
            "slot_centerline_span_mm": [10.7, 18.3],
            "slot_void_span_mm": [9.8, 19.2],
            "slot_width_mm": 4.2,
            "predicted_pallet_half_swing_deg": round(math.degrees(math.asin(3.0 / 14.5)), 3),
            "blocked_claims": ["watch-grade escapement", "regulating balance", "lock/drop/impulse verified"],
        },
        "balance_drive_model": {
            "type": "pallet_output_pin_to_balance_radial_slot",
            "claim": "pallet output pin is captured by a balance receiver slot, producing a bounded carrier-mounted balance display; this is non-regulating and does not claim lock/drop/impulse.",
            "pallet_axis_mm": [26.0, 0.0],
            "balance_axis_mm": [-18.0, 10.0],
            "pallet_output_pin_radius_mm": 1.2,
            "pallet_output_pin_offset_mm": 35.0,
            "pallet_output_pin_zero_angle_deg": 167.1957,
            "slot_zero_angle_deg": -12.8043,
            "slot_centerline_span_mm": [8.2, 13.5],
            "slot_width_mm": 3.2,
            "predicted_balance_half_swing_deg": 33.6489,
            "blocked_claims": [
                "watch-grade escapement",
                "regulating balance",
                "self-sustaining oscillation",
                "lock/drop/impulse verified",
            ],
        },
        "required_gates": [
            "v28_connected_geometry_pass",
            "v28_internal_ring_geometry_pass",
            "v28_support_bom_closure_pass",
            "v28_support_geometry_pass",
            "v28_escapement_contact_truth_pass",
            "v28_full_cycle_motion_pass",
            "v28_declared_contact_pass",
            "v28_balance_drive_truth_pass",
            "v28_claim_boundary_pass",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    guidance_by_part = {item["part"]: item for item in manifest["print_guidance"]}
    with (OUT / "printed_parts.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["part", "qty", "stl", "step", "solid_count", "orientation_note", "support_note", "postprocess_note"],
        )
        writer.writeheader()
        for item in stats:
            guidance = guidance_by_part[item["name"]]
            writer.writerow(
                {
                    "part": item["name"],
                    "qty": guidance["qty"],
                    "stl": item["stl"],
                    "step": item["step"],
                    "solid_count": item["solid_count"],
                    "orientation_note": guidance["orientation_note"],
                    "support_note": guidance["support_note"],
                    "postprocess_note": guidance["postprocess_note"],
                }
            )
    print(json.dumps({"status": "candidate_generated", "manifest": str(MANIFEST), "part_count": len(stats)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

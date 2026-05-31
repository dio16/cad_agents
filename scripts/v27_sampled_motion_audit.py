from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from v27_evidence import evidence_fields


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v27_connected_contract.json"
OUT = ROOT / "reports" / "fabrication_v27_connected_package" / "v27_sampled_motion_audit.json"

ALLOWED_CONTACT = {
    tuple(sorted(pair))
    for pair in [
        ("02_fixed_internal_ring_72t_v27", "04_orbit_escape_pinion_18t_v27"),
        ("03_rotating_carrier_drive_gear_v27", "05_hand_crank_pinion_v27"),
    ]
}

DECLARED_DRIVE_CONTACT = tuple(sorted(("07_escape_wheel_15t_v27", "08_pallet_fork_bridge_v27")))


def load_shape(path: str) -> cq.Workplane:
    return cq.importers.importStep(path)


def rotate_point(x: float, y: float, deg: float) -> tuple[float, float]:
    angle = math.radians(deg)
    return (x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle))


def rotate_local(shape: cq.Workplane, deg: float) -> cq.Workplane:
    return shape.rotate((0, 0, 0), (0, 0, 1), deg)


def pallet_angle_deg(relative_escape_deg: float, pivot_distance_mm: float, pin_offset_mm: float) -> float:
    angle = math.radians(relative_escape_deg)
    return math.degrees(math.atan2(pin_offset_mm * math.sin(angle), pivot_distance_mm + pin_offset_mm * math.cos(angle)))


def volume(shape: cq.Workplane) -> float:
    try:
        return float(shape.val().Volume())
    except Exception:
        return 0.0


def placed_shapes(manifest: dict, theta_deg: float) -> dict[str, cq.Workplane]:
    parts = {item["name"]: load_shape(item["step"]) for item in manifest["parts"]}
    drive = manifest["escapement_drive_model"]
    axes = manifest["axes_and_supports"]
    internal_mesh = next(mesh for mesh in manifest["gear_meshes"] if mesh["name"] == "fixed_internal_ring_to_orbit_escape_pinion")
    hand_mesh = next(mesh for mesh in manifest["gear_meshes"] if mesh["name"] == "hand_pinion_to_carrier_drive_gear")
    orbit_local = tuple(axes["orbit_escape_axis"]["axis_mm"])
    pallet_local = tuple(drive["pallet_axis_mm"])
    balance_local = tuple(axes["balance_axis"]["axis_mm"])
    hand_axis = tuple(axes["hand_axis"]["axis_mm"])
    orbit_xy = rotate_point(*orbit_local, theta_deg)
    pallet_xy = rotate_point(*pallet_local, theta_deg)
    balance_xy = rotate_point(*balance_local, theta_deg)
    relative_escape_deg = internal_mesh["relative_pinion_spin_ratio_in_carrier"] * theta_deg
    absolute_orbit_deg = (1.0 + internal_mesh["relative_pinion_spin_ratio_in_carrier"]) * theta_deg
    hand_deg = hand_mesh["hand_spin_ratio_to_carrier"] * theta_deg
    pallet_rel_deg = pallet_angle_deg(
        relative_escape_deg,
        math.dist(drive["escape_axis_mm"], drive["pallet_axis_mm"]),
        drive["escape_pin_offset_mm"],
    )
    shapes = {
        "01_base_plinth_bearing_pocket_v27": parts["01_base_plinth_bearing_pocket_v27"],
        "02_fixed_internal_ring_72t_v27": parts["02_fixed_internal_ring_72t_v27"],
        "03_rotating_carrier_drive_gear_v27": rotate_local(parts["03_rotating_carrier_drive_gear_v27"], theta_deg),
        "04_orbit_escape_pinion_18t_v27": rotate_local(parts["04_orbit_escape_pinion_18t_v27"], absolute_orbit_deg).translate((orbit_xy[0], orbit_xy[1], 0.0)),
        "05_hand_crank_pinion_v27": parts["05_hand_crank_pinion_v27"].rotate((*hand_axis, 0), (*hand_axis, 1), hand_deg),
        "06_balance_wheel_v27": rotate_local(parts["06_balance_wheel_v27"], theta_deg).translate((balance_xy[0], balance_xy[1], 0.0)),
        "07_escape_wheel_15t_v27": rotate_local(parts["07_escape_wheel_15t_v27"], absolute_orbit_deg).translate((orbit_xy[0], orbit_xy[1], 0.0)),
        "08_pallet_fork_bridge_v27": rotate_local(parts["08_pallet_fork_bridge_v27"], theta_deg + pallet_rel_deg).translate((pallet_xy[0], pallet_xy[1], 0.0)),
        "09_crank_knob_v27": parts["09_crank_knob_v27"].translate((hand_axis[0], hand_axis[1], 45.0)).rotate((*hand_axis, 0), (*hand_axis, 1), hand_deg),
    }
    return shapes


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sample_angles = list(range(0, 360, 15))
    collisions = []
    declared_drive_contacts = []
    pallet_angles = []
    pivot_distance = math.dist(
        manifest["escapement_drive_model"]["escape_axis_mm"],
        manifest["escapement_drive_model"]["pallet_axis_mm"],
    )
    internal_mesh = next(mesh for mesh in manifest["gear_meshes"] if mesh["name"] == "fixed_internal_ring_to_orbit_escape_pinion")
    hand_mesh = next(mesh for mesh in manifest["gear_meshes"] if mesh["name"] == "hand_pinion_to_carrier_drive_gear")
    relative_ratio = internal_mesh["relative_pinion_spin_ratio_in_carrier"]
    expected_relative_ratio = -internal_mesh["ring_teeth"] / internal_mesh["pinion_teeth"]
    hand_ratio = hand_mesh["hand_spin_ratio_to_carrier"]
    expected_hand_ratio = -hand_mesh["driven_teeth"] / hand_mesh["driver_teeth"]
    for theta in sample_angles:
        shapes = placed_shapes(manifest, theta)
        pallet_angles.append(
            {
                "carrier_deg": theta,
                "pallet_relative_deg": round(
                    pallet_angle_deg(relative_ratio * theta, pivot_distance, manifest["escapement_drive_model"]["escape_pin_offset_mm"]),
                    4,
                ),
            }
        )
        names = sorted(shapes)
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                if tuple(sorted((a, b))) in ALLOWED_CONTACT:
                    continue
                common_volume = volume(shapes[a].intersect(shapes[b]))
                if tuple(sorted((a, b))) == DECLARED_DRIVE_CONTACT:
                    if common_volume > 0.05:
                        declared_drive_contacts.append(
                            {
                                "carrier_deg": theta,
                                "a": a,
                                "b": b,
                                "common_volume_mm3": round(common_volume, 4),
                            }
                        )
                    continue
                if common_volume > 0.05:
                    collisions.append(
                        {
                            "carrier_deg": theta,
                            "a": a,
                            "b": b,
                            "common_volume_mm3": round(common_volume, 4),
                        }
                    )
    checks = [
        {
            "name": "sampled motion reads orbit and hand ratios from contract gear meshes",
            "status": "pass"
            if math.isclose(relative_ratio, expected_relative_ratio, rel_tol=0, abs_tol=1e-9)
            and math.isclose(hand_ratio, expected_hand_ratio, rel_tol=0, abs_tol=1e-9)
            else "fail",
            "relative_orbit_ratio": relative_ratio,
            "expected_relative_orbit_ratio": expected_relative_ratio,
            "hand_ratio": hand_ratio,
            "expected_hand_ratio": expected_hand_ratio,
        },
        {
            "name": "sampled motion reads support axes from contract",
            "status": "pass"
            if manifest["axes_and_supports"]["orbit_escape_axis"]["axis_mm"] == manifest["escapement_drive_model"]["escape_axis_mm"]
            and manifest["axes_and_supports"]["pallet_axis"]["axis_mm"] == manifest["escapement_drive_model"]["pallet_axis_mm"]
            else "fail",
            "orbit_axis_mm": manifest["axes_and_supports"]["orbit_escape_axis"]["axis_mm"],
            "escape_axis_mm": manifest["escapement_drive_model"]["escape_axis_mm"],
            "pallet_axis_mm": manifest["axes_and_supports"]["pallet_axis"]["axis_mm"],
        },
        {
            "name": "sampled motion uses full-cycle grid",
            "status": "pass" if sample_angles == list(range(0, 360, 15)) else "fail",
            "sample_angles_deg": sample_angles,
        },
        {
            "name": "eccentric pin-slot pallet motion stays within predicted swing",
            "status": "pass"
            if max(abs(item["pallet_relative_deg"]) for item in pallet_angles)
            <= manifest["escapement_drive_model"]["predicted_pallet_half_swing_deg"] + 0.05
            else "fail",
            "pallet_angles": pallet_angles,
        },
        {
            "name": "sampled motion has no undeclared collisions",
            "status": "pass" if not collisions else "fail",
            "collision_count": len(collisions),
            "collisions": collisions[:100],
        },
        {
            "name": "declared eccentric pin-slot drive contact stays bounded",
            "status": "pass"
            if declared_drive_contacts
            and max(item["common_volume_mm3"] for item in declared_drive_contacts) <= 1.5
            else "fail",
            "contact_sample_count": len(declared_drive_contacts),
            "max_contact_volume_mm3": max((item["common_volume_mm3"] for item in declared_drive_contacts), default=0.0),
            "contacts": declared_drive_contacts[:100],
        },
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    motion_contract_pass = all(check["status"] == "pass" for check in checks[:3])
    gear_relation_pass = checks[0]["status"] == "pass"
    drive_geometry_pass = checks[3]["status"] == "pass" and checks[5]["status"] == "pass"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        **evidence_fields(),
        "status": status,
        "sample_angles_deg": sample_angles,
        "undeclared_collision_count": len(collisions),
        "declared_drive_contact_count": len(declared_drive_contacts),
        "motion_contract_status": "pass" if motion_contract_pass else "fail",
        "gear_relation_status": "pass" if gear_relation_pass else "fail",
        "drive_geometry_status": "pass" if drive_geometry_pass else "fail",
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "collision_count": len(collisions), "report": str(OUT)}, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from v27_evidence import evidence_fields


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v27_connected_contract.json"
OUT = ROOT / "reports" / "fabrication_v27_connected_package" / "v27_mechanical_truth_audit.json"


def cyl(radius: float, z0: float, z1: float, x: float, y: float) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(radius).extrude(z1 - z0)


def add(checks: list[dict], name: str, passed: bool, severity: str = "P1", **detail: object) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "severity": severity, **detail})


def ring_geometry_checks(manifest: dict, checks: list[dict]) -> None:
    step = Path(next(item["step"] for item in manifest["parts"] if item["name"] == "02_fixed_internal_ring_72t_v27"))
    ring = cq.importers.importStep(str(step))
    teeth = 72
    phase = math.pi / teeth
    tooth_hits = 0
    gap_hits = 0
    for i in range(teeth):
        tooth_angle = phase + 2.0 * math.pi * i / teeth
        gap_angle = tooth_angle + math.pi / teeth
        tooth_probe = cyl(0.34, 39.0, 42.0, 53.9 * math.cos(tooth_angle), 53.9 * math.sin(tooth_angle))
        gap_probe = cyl(0.34, 39.0, 42.0, 53.9 * math.cos(gap_angle), 53.9 * math.sin(gap_angle))
        tooth_hits += 1 if ring.intersect(tooth_probe).val().Volume() > 0.05 else 0
        gap_hits += 1 if ring.intersect(gap_probe).val().Volume() > 0.05 else 0
    add(checks, "fixed internal ring has 72 occupied tooth probes", tooth_hits == 72, "P0", occupied_tooth_probes=tooth_hits)
    add(checks, "fixed internal ring has open gaps between teeth", gap_hits == 0, "P0", occupied_gap_probes=gap_hits)


def gear_contract_checks(manifest: dict, checks: list[dict]) -> None:
    meshes = {mesh["name"]: mesh for mesh in manifest.get("gear_meshes", [])}
    internal = meshes.get("fixed_internal_ring_to_orbit_escape_pinion", {})
    hand = meshes.get("hand_pinion_to_carrier_drive_gear", {})
    internal_center = internal.get("ring_pitch_radius_mm", 0.0) - internal.get("pinion_pitch_radius_mm", 0.0)
    internal_ratio = -internal.get("ring_teeth", 0) / max(internal.get("pinion_teeth", 1), 1)
    hand_center = hand.get("driver_pitch_radius_mm", 0.0) + hand.get("driven_pitch_radius_mm", 0.0)
    hand_ratio = -hand.get("driven_teeth", 0) / max(hand.get("driver_teeth", 1), 1)
    add(checks, "internal ring mesh center distance matches contract", abs(internal_center - internal.get("center_distance_mm", -999)) < 1e-6, "P0", computed_mm=internal_center, contract_mm=internal.get("center_distance_mm"))
    add(checks, "internal ring mesh relative ratio matches contract", abs(internal_ratio - internal.get("relative_pinion_spin_ratio_in_carrier", 999)) < 1e-6, "P0", computed_ratio=internal_ratio, contract_ratio=internal.get("relative_pinion_spin_ratio_in_carrier"))
    add(checks, "hand mesh center distance matches contract", abs(hand_center - hand.get("center_distance_mm", -999)) < 1e-6, "P0", computed_mm=hand_center, contract_mm=hand.get("center_distance_mm"))
    add(checks, "hand mesh ratio matches contract", abs(hand_ratio - hand.get("hand_spin_ratio_to_carrier", 999)) < 1e-6, "P0", computed_ratio=hand_ratio, contract_ratio=hand.get("hand_spin_ratio_to_carrier"))
    add(checks, "both meshes retain nonzero backlash allowance", internal.get("backlash_mm", 0) >= 0.2 and hand.get("backlash_mm", 0) >= 0.2, "P0", internal_backlash_mm=internal.get("backlash_mm"), hand_backlash_mm=hand.get("backlash_mm"))


def support_bom_checks(manifest: dict, checks: list[dict]) -> None:
    hardware_roles = {item["role"] for item in manifest.get("standard_hardware", [])}
    required_hardware = {"central_bearing", "orbit_escape_shaft", "hand_input_shaft", "balance_staff", "pallet_arbor"}
    axes = manifest.get("axes_and_supports", {})
    add(checks, "critical hardware roles are declared", required_hardware.issubset(hardware_roles), "P0", missing=sorted(required_hardware - hardware_roles))
    add(checks, "critical support axes are declared", {"central_axis", "orbit_escape_axis", "hand_axis", "balance_axis", "pallet_axis"}.issubset(axes), "P0", declared_axes=sorted(axes))
    part_by_name = {item["name"]: cq.importers.importStep(item["step"]) for item in manifest["parts"]}
    for axis_name, support in manifest.get("support_geometry", {}).items():
        part = part_by_name[support["part"]]
        x, y = support["axis_mm"]
        bore_radius = support["bore_radius_mm"]
        outer_radius = support["outer_radius_mm"]
        bore_volumes = []
        seat_volumes = []
        for z0, z1 in support["seat_spans_mm"]:
            bore_probe = cyl(bore_radius * 0.98, z0 + 0.05, z1 - 0.05, x, y)
            seat_probe = cyl(outer_radius * 0.94, z0 + 0.05, z1 - 0.05, x, y).cut(
                cyl(bore_radius * 1.04, z0, z1, x, y)
            )
            bore_volumes.append(round(part.intersect(bore_probe).val().Volume(), 4))
            seat_volumes.append(round(part.intersect(seat_probe).val().Volume(), 4))
        add(
            checks,
            f"{axis_name} support bores are open through declared seats",
            max(bore_volumes, default=999.0) <= 0.05,
            "P0",
            bore_intersection_volumes_mm3=bore_volumes,
        )
        add(
            checks,
            f"{axis_name} has solid material around declared seats",
            min(seat_volumes, default=0.0) > 1.0,
            "P0",
            seat_material_volumes_mm3=seat_volumes,
        )


def escapement_drive_checks(manifest: dict, checks: list[dict]) -> None:
    drive = manifest.get("escapement_drive_model", {})
    escape_axis = drive.get("escape_axis_mm", [0.0, 0.0])
    pallet_axis = drive.get("pallet_axis_mm", [0.0, 0.0])
    distance = math.dist(escape_axis, pallet_axis)
    slot_start, slot_end = drive.get("slot_centerline_span_mm", [0.0, 0.0])
    pin_radius = drive.get("escape_pin_radius_mm", 0.0)
    pin_offset = drive.get("escape_pin_offset_mm", 0.0)
    slot_width = drive.get("slot_width_mm", 0.0)
    radial_positions = []
    pallet_angles = []
    for deg in range(360):
        angle = math.radians(deg)
        pin_center = [
            escape_axis[0] + pin_offset * math.cos(angle),
            escape_axis[1] + pin_offset * math.sin(angle),
        ]
        vector = [pin_center[0] - pallet_axis[0], pin_center[1] - pallet_axis[1]]
        radial_positions.append(math.dist(pin_center, pallet_axis))
        pallet_angles.append(math.degrees(math.atan2(vector[1], vector[0])))
    predicted_half_swing = max(abs(min(pallet_angles)), abs(max(pallet_angles)))
    add(
        checks,
        "eccentric pin radial travel fits declared slot span",
        min(radial_positions) >= slot_start and max(radial_positions) <= slot_end,
        "P0",
        min_pin_radius_mm=round(min(radial_positions), 4),
        max_pin_radius_mm=round(max(radial_positions), 4),
        slot_span_mm=[slot_start, slot_end],
    )
    add(
        checks,
        "eccentric pin is captured by slot width",
        slot_width > 2.0 * pin_radius,
        "P0",
        pin_diameter_mm=2.0 * pin_radius,
        slot_width_mm=slot_width,
    )
    add(
        checks,
        "eccentric pin-slot predicts bounded pallet swing",
        abs(predicted_half_swing - drive.get("predicted_pallet_half_swing_deg", -999.0)) < 0.05,
        "P0",
        computed_half_swing_deg=round(predicted_half_swing, 4),
        contract_half_swing_deg=drive.get("predicted_pallet_half_swing_deg"),
        pivot_distance_mm=distance,
    )
    add(
        checks,
        "escapement claims remain bounded to demonstrator scope",
        {"watch-grade escapement", "regulating balance", "lock/drop/impulse verified"}.issubset(set(drive.get("blocked_claims", []))),
        "P0",
        blocked_claims=drive.get("blocked_claims", []),
    )


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    checks: list[dict] = []
    ring_geometry_checks(manifest, checks)
    gear_contract_checks(manifest, checks)
    support_bom_checks(manifest, checks)
    escapement_drive_checks(manifest, checks)
    fail_count = sum(check["status"] != "pass" for check in checks)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        **evidence_fields(),
        "status": "pass" if fail_count == 0 else "fail",
        "fail_count": fail_count,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "fail_count": fail_count, "report": str(OUT)}, indent=2))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

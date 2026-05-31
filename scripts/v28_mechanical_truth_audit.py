from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifests' / 'tourbillon_v28_mechanism_contract.json'
OUT = ROOT / 'reports' / 'fabrication_v28_mechanism_package' / 'v28_mechanical_truth_audit.json'


def add(checks: list[dict], name: str, passed: bool, **detail: object) -> None:
    checks.append({'name': name, 'status': 'pass' if passed else 'fail', **detail})


def cyl(radius: float, z0: float, z1: float, x: float, y: float) -> cq.Workplane:
    return cq.Workplane('XY').workplane(offset=z0).center(x, y).circle(radius).extrude(z1 - z0)


def ring_geometry_checks(manifest: dict, checks: list[dict]) -> None:
    ring_path = next(item['step'] for item in manifest['parts'] if item['name'] == '02_fixed_internal_ring_72t_v28')
    ring = cq.importers.importStep(ring_path)
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
    add(checks, 'fixed internal ring has 72 occupied tooth probes', tooth_hits == 72, occupied_tooth_probes=tooth_hits)
    add(checks, 'fixed internal ring has open gaps between teeth', gap_hits == 0, occupied_gap_probes=gap_hits)


def mesh_checks(manifest: dict, checks: list[dict]) -> None:
    meshes = {mesh['name']: mesh for mesh in manifest['gear_meshes']}
    internal = meshes['fixed_internal_ring_to_orbit_escape_pinion']
    hand = meshes['hand_pinion_to_carrier_drive_gear']
    add(checks, 'internal-ring center distance matches contract', math.isclose(internal['ring_pitch_radius_mm'] - internal['pinion_pitch_radius_mm'], internal['center_distance_mm'], abs_tol=1e-9))
    add(checks, 'internal-ring ratio matches contract', math.isclose(-internal['ring_teeth'] / internal['pinion_teeth'], internal['relative_pinion_spin_ratio_in_carrier'], abs_tol=1e-9))
    add(checks, 'hand mesh center distance matches contract', math.isclose(hand['driver_pitch_radius_mm'] + hand['driven_pitch_radius_mm'], hand['center_distance_mm'], abs_tol=1e-9))
    add(checks, 'hand mesh ratio matches contract', math.isclose(-hand['driven_teeth'] / hand['driver_teeth'], hand['hand_spin_ratio_to_carrier'], abs_tol=1e-9))


def balance_drive_checks(manifest: dict, checks: list[dict]) -> None:
    drive = manifest['balance_drive_model']
    pallet_half_swing = manifest['escapement_drive_model']['predicted_pallet_half_swing_deg']
    pallet_axis = tuple(drive['pallet_axis_mm'])
    balance_axis = tuple(drive['balance_axis_mm'])
    radii = []
    angles = []
    for i in range(241):
        pallet_deg = -pallet_half_swing + (2.0 * pallet_half_swing * i / 240.0)
        output_deg = drive['pallet_output_pin_zero_angle_deg'] + pallet_deg
        pin = (
            pallet_axis[0] + drive['pallet_output_pin_offset_mm'] * math.cos(math.radians(output_deg)),
            pallet_axis[1] + drive['pallet_output_pin_offset_mm'] * math.sin(math.radians(output_deg)),
        )
        vector = (pin[0] - balance_axis[0], pin[1] - balance_axis[1])
        radii.append(math.dist(pin, balance_axis))
        angles.append(math.degrees(math.atan2(vector[1], vector[0])) - drive['slot_zero_angle_deg'])
    add(checks, 'balance receiver slot captures pallet output pin radial travel', min(radii) >= drive['slot_centerline_span_mm'][0] and max(radii) <= drive['slot_centerline_span_mm'][1], min_radius_mm=round(min(radii), 4), max_radius_mm=round(max(radii), 4), slot_span_mm=drive['slot_centerline_span_mm'])
    add(checks, 'balance receiver slot width captures output pin diameter', drive['slot_width_mm'] > 2.0 * drive['pallet_output_pin_radius_mm'], slot_width_mm=drive['slot_width_mm'], pin_diameter_mm=2.0 * drive['pallet_output_pin_radius_mm'])
    add(checks, 'balance linkage predicts bounded oscillation', math.isclose(max(abs(min(angles)), abs(max(angles))), drive['predicted_balance_half_swing_deg'], abs_tol=0.15), computed_half_swing_deg=round(max(abs(min(angles)), abs(max(angles))), 4), contract_half_swing_deg=drive['predicted_balance_half_swing_deg'])
    add(checks, 'claim remains non-watch-grade', {'watch-grade escapement', 'regulating balance', 'self-sustaining oscillation', 'lock/drop/impulse verified'}.issubset(set(drive['blocked_claims'])), blocked_claims=drive['blocked_claims'])
    chain = manifest.get('drive_chain', [])
    add(
        checks,
        'drive chain closes from hand input through pallet into balance',
        any(item.get('from') == 'pallet_fork' and item.get('to') == 'balance_wheel' for item in chain)
        and any(item.get('from') == 'escape_wheel' and item.get('to') == 'pallet_fork' for item in chain),
        drive_chain=chain,
    )


def part_checks(manifest: dict, checks: list[dict]) -> None:
    for item in manifest['parts']:
        step = Path(item['step'])
        stl = Path(item['stl'])
        add(checks, f"{item['name']} STEP exists", step.exists() and step.stat().st_size > 1000, path=str(step))
        add(checks, f"{item['name']} STL exists", stl.exists() and stl.stat().st_size > 1000, path=str(stl))
        if step.exists():
            solid_count = len(cq.importers.importStep(str(step)).val().Solids())
            add(checks, f"{item['name']} imports as one OCP solid", solid_count == 1, solid_count=solid_count)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    checks: list[dict] = []
    part_checks(manifest, checks)
    ring_geometry_checks(manifest, checks)
    mesh_checks(manifest, checks)
    balance_drive_checks(manifest, checks)
    status = 'pass' if all(check['status'] == 'pass' for check in checks) else 'fail'
    OUT.write_text(json.dumps({'created_at': datetime.now(timezone.utc).isoformat(), 'status': status, 'checks': checks}, indent=2), encoding='utf-8')
    print(json.dumps({'status': status, 'report': str(OUT)}, indent=2))
    return 0 if status == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())

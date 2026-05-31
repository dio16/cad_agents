from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifests' / 'tourbillon_v28_mechanism_contract.json'
OUT = ROOT / 'reports' / 'fabrication_v28_mechanism_package' / 'v28_sampled_motion_audit.json'

ALLOWED_CONTACT = {
    tuple(sorted(pair))
    for pair in [
        ('02_fixed_internal_ring_72t_v28', '04_orbit_escape_pinion_18t_v28'),
        ('03_rotating_carrier_drive_gear_v28', '05_hand_crank_pinion_v28'),
    ]
}
DECLARED_CONTACTS = {
    tuple(sorted(('07_escape_wheel_15t_v28', '08_pallet_fork_bridge_v28'))),
    tuple(sorted(('06_balance_wheel_v28', '08_pallet_fork_bridge_v28'))),
}


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


def balance_angle_deg(manifest: dict, pallet_relative_deg: float) -> tuple[float, float]:
    drive = manifest['balance_drive_model']
    pallet_axis = tuple(drive['pallet_axis_mm'])
    balance_axis = tuple(drive['balance_axis_mm'])
    output_angle = drive['pallet_output_pin_zero_angle_deg'] + pallet_relative_deg
    dx, dy = rotate_point(drive['pallet_output_pin_offset_mm'], 0.0, output_angle)
    pin = (pallet_axis[0] + dx, pallet_axis[1] + dy)
    vector = (pin[0] - balance_axis[0], pin[1] - balance_axis[1])
    angle = math.degrees(math.atan2(vector[1], vector[0])) - drive['slot_zero_angle_deg']
    return angle, math.dist(pin, balance_axis)


def volume(shape: cq.Workplane) -> float:
    try:
        return float(shape.val().Volume())
    except Exception:
        return 0.0


def placed_shapes(manifest: dict, theta_deg: float) -> tuple[dict[str, cq.Workplane], float, float, float]:
    parts = {item['name']: load_shape(item['step']) for item in manifest['parts']}
    escapement = manifest['escapement_drive_model']
    axes = manifest['axes_and_supports']
    internal_mesh = next(mesh for mesh in manifest['gear_meshes'] if mesh['name'] == 'fixed_internal_ring_to_orbit_escape_pinion')
    hand_mesh = next(mesh for mesh in manifest['gear_meshes'] if mesh['name'] == 'hand_pinion_to_carrier_drive_gear')
    orbit_local = tuple(axes['orbit_escape_axis']['axis_mm'])
    pallet_local = tuple(axes['pallet_axis']['axis_mm'])
    balance_local = tuple(axes['balance_axis']['axis_mm'])
    hand_axis = tuple(axes['hand_axis']['axis_mm'])
    orbit_xy = rotate_point(*orbit_local, theta_deg)
    pallet_xy = rotate_point(*pallet_local, theta_deg)
    balance_xy = rotate_point(*balance_local, theta_deg)
    relative_escape_deg = internal_mesh['relative_pinion_spin_ratio_in_carrier'] * theta_deg
    absolute_orbit_deg = (1.0 + internal_mesh['relative_pinion_spin_ratio_in_carrier']) * theta_deg
    hand_deg = hand_mesh['hand_spin_ratio_to_carrier'] * theta_deg
    pallet_rel_deg = pallet_angle_deg(relative_escape_deg, math.dist(escapement['escape_axis_mm'], escapement['pallet_axis_mm']), escapement['escape_pin_offset_mm'])
    balance_rel_deg, pin_radius = balance_angle_deg(manifest, pallet_rel_deg)
    shapes = {
        '01_base_plinth_bearing_pocket_v28': parts['01_base_plinth_bearing_pocket_v28'],
        '02_fixed_internal_ring_72t_v28': parts['02_fixed_internal_ring_72t_v28'],
        '03_rotating_carrier_drive_gear_v28': rotate_local(parts['03_rotating_carrier_drive_gear_v28'], theta_deg),
        '04_orbit_escape_pinion_18t_v28': rotate_local(parts['04_orbit_escape_pinion_18t_v28'], absolute_orbit_deg).translate((orbit_xy[0], orbit_xy[1], 0.0)),
        '05_hand_crank_pinion_v28': parts['05_hand_crank_pinion_v28'].rotate((*hand_axis, 0), (*hand_axis, 1), hand_deg),
        '06_balance_wheel_v28': rotate_local(parts['06_balance_wheel_v28'], theta_deg + balance_rel_deg).translate((balance_xy[0], balance_xy[1], 0.0)),
        '07_escape_wheel_15t_v28': rotate_local(parts['07_escape_wheel_15t_v28'], absolute_orbit_deg).translate((orbit_xy[0], orbit_xy[1], 0.0)),
        '08_pallet_fork_bridge_v28': rotate_local(parts['08_pallet_fork_bridge_v28'], theta_deg + pallet_rel_deg).translate((pallet_xy[0], pallet_xy[1], 0.0)),
        '09_crank_knob_v28': parts['09_crank_knob_v28'].translate((hand_axis[0], hand_axis[1], 45.0)).rotate((*hand_axis, 0), (*hand_axis, 1), hand_deg),
    }
    return shapes, pallet_rel_deg, balance_rel_deg, pin_radius


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    sample_angles = list(range(0, 360, 15))
    collisions = []
    declared_contacts: dict[str, list[dict]] = {'escape_to_pallet': [], 'pallet_to_balance': []}
    pallet_samples = []
    balance_samples = []
    for theta in sample_angles:
        shapes, pallet_rel, balance_rel, pin_radius = placed_shapes(manifest, theta)
        pallet_samples.append({'carrier_deg': theta, 'pallet_relative_deg': round(pallet_rel, 4)})
        balance_samples.append({'carrier_deg': theta, 'balance_relative_deg': round(balance_rel, 4), 'pin_radius_from_balance_mm': round(pin_radius, 4)})
        names = sorted(shapes)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                pair = tuple(sorted((a, b)))
                if pair in ALLOWED_CONTACT:
                    continue
                common_volume = volume(shapes[a].intersect(shapes[b]))
                if pair in DECLARED_CONTACTS:
                    key = 'escape_to_pallet' if '07_escape_wheel_15t_v28' in pair else 'pallet_to_balance'
                    if common_volume > 0.05:
                        declared_contacts[key].append({'carrier_deg': theta, 'a': a, 'b': b, 'common_volume_mm3': round(common_volume, 4)})
                    continue
                if common_volume > 0.05:
                    collisions.append({'carrier_deg': theta, 'a': a, 'b': b, 'common_volume_mm3': round(common_volume, 4)})
    drive = manifest['balance_drive_model']
    checks = [
        {
            'name': 'sampled motion uses full-cycle grid',
            'status': 'pass' if sample_angles == list(range(0, 360, 15)) else 'fail',
            'sample_angles_deg': sample_angles,
        },
        {
            'name': 'pallet motion stays within manifest prediction',
            'status': 'pass' if max(abs(item['pallet_relative_deg']) for item in pallet_samples) <= manifest['escapement_drive_model']['predicted_pallet_half_swing_deg'] + 0.05 else 'fail',
            'samples': pallet_samples,
        },
        {
            'name': 'balance motion stays within manifest prediction',
            'status': 'pass' if max(abs(item['balance_relative_deg']) for item in balance_samples) <= drive['predicted_balance_half_swing_deg'] + 0.05 else 'fail',
            'samples': balance_samples,
        },
        {
            'name': 'balance receiver slot captures output-pin radial travel',
            'status': 'pass' if min(item['pin_radius_from_balance_mm'] for item in balance_samples) >= drive['slot_centerline_span_mm'][0] and max(item['pin_radius_from_balance_mm'] for item in balance_samples) <= drive['slot_centerline_span_mm'][1] else 'fail',
            'slot_span_mm': drive['slot_centerline_span_mm'],
            'samples': balance_samples,
        },
        {
            'name': 'sampled motion has no undeclared collisions',
            'status': 'pass' if not collisions else 'fail',
            'collision_count': len(collisions),
            'collisions': collisions[:100],
        },
        {
            'name': 'declared escape-to-pallet drive contact remains bounded',
            'status': 'pass' if declared_contacts['escape_to_pallet'] and max(item['common_volume_mm3'] for item in declared_contacts['escape_to_pallet']) <= 1.5 else 'fail',
            'contacts': declared_contacts['escape_to_pallet'][:100],
        },
        {
            'name': 'declared pallet-to-balance drive contact remains bounded',
            'status': 'pass' if max((item['common_volume_mm3'] for item in declared_contacts['pallet_to_balance']), default=0.0) <= 1.5 else 'fail',
            'contacts': declared_contacts['pallet_to_balance'][:100],
        },
    ]
    status = 'pass' if all(check['status'] == 'pass' for check in checks) else 'fail'
    report = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'sample_angles_deg': sample_angles,
        'undeclared_collision_count': len(collisions),
        'declared_contact_counts': {key: len(value) for key, value in declared_contacts.items()},
        'checks': checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status': status, 'collision_count': len(collisions), 'report': str(OUT)}, indent=2))
    return 0 if status == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())

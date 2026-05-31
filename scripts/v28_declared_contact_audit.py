from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from v28_sampled_motion_audit import placed_shapes

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifests' / 'tourbillon_v28_mechanism_contract.json'
OUT = ROOT / 'reports' / 'fabrication_v28_mechanism_package' / 'v28_declared_contact_audit.json'

DECLARED_PAIRS = [
    ('02_fixed_internal_ring_72t_v28', '04_orbit_escape_pinion_18t_v28', 'mesh_clearance'),
    ('03_rotating_carrier_drive_gear_v28', '05_hand_crank_pinion_v28', 'mesh_clearance'),
    ('07_escape_wheel_15t_v28', '08_pallet_fork_bridge_v28', 'drive_contact'),
    ('06_balance_wheel_v28', '08_pallet_fork_bridge_v28', 'drive_contact'),
]


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    samples = []
    for theta in range(0, 360, 15):
        shapes, _, _, _ = placed_shapes(manifest, theta)
        for a, b, kind in DECLARED_PAIRS:
            volume = float(shapes[a].intersect(shapes[b]).val().Volume())
            samples.append({'carrier_deg': theta, 'a': a, 'b': b, 'kind': kind, 'common_volume_mm3': round(volume, 4)})
    checks = []
    for a, b, kind in DECLARED_PAIRS:
        volumes = [sample['common_volume_mm3'] for sample in samples if sample['a'] == a and sample['b'] == b]
        if kind == 'mesh_clearance':
            passed = max(volumes) <= 0.05
        else:
            passed = max(volumes) <= 1.5
        checks.append({'name': f'{a}::{b} {kind} stays within declared envelope', 'status': 'pass' if passed else 'fail', 'max_common_volume_mm3': max(volumes), 'min_common_volume_mm3': min(volumes)})
    drive = manifest['balance_drive_model']
    radial_samples = []
    for theta in range(0, 360, 15):
        _, _, _, pin_radius = placed_shapes(manifest, theta)
        radial_samples.append(pin_radius)
    checks.append(
        {
            'name': 'pallet-to-balance relation is explicitly declared and radially captured',
            'status': 'pass'
            if drive['type'] == 'pallet_output_pin_to_balance_radial_slot'
            and min(radial_samples) >= drive['slot_centerline_span_mm'][0]
            and max(radial_samples) <= drive['slot_centerline_span_mm'][1]
            else 'fail',
            'declared_relation': drive['type'],
            'slot_span_mm': drive['slot_centerline_span_mm'],
            'min_pin_radius_mm': round(min(radial_samples), 4),
            'max_pin_radius_mm': round(max(radial_samples), 4),
        }
    )
    status = 'pass' if all(check['status'] == 'pass' for check in checks) else 'fail'
    OUT.write_text(json.dumps({'created_at': datetime.now(timezone.utc).isoformat(), 'status': status, 'checks': checks, 'samples': samples}, indent=2), encoding='utf-8')
    print(json.dumps({'status': status, 'report': str(OUT)}, indent=2))
    return 0 if status == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())

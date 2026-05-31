from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIN = ROOT / 'manifests' / 'tourbillon_v31_kinematic_contract.json'
ROLE = ROOT / 'reports' / 'fabrication_v31_geometry_candidate' / 'v31_role_manifest.json'
OUT = ROOT / 'reports' / 'fabrication_v31_geometry_candidate' / 'v31_motion_validation.json'


def main() -> int:
    kin = json.loads(KIN.read_text(encoding='utf-8'))
    role = json.loads(ROLE.read_text(encoding='utf-8'))
    meshes = {mesh['name']: mesh for mesh in kin['meshes']}
    barrel_to_lower = meshes['barrel_to_lower_transfer']
    upper_to_carrier = meshes['upper_transfer_to_carrier']
    lower_ratio_to_barrel = barrel_to_lower['driver_teeth'] / barrel_to_lower['driven_teeth']
    carrier_ratio_to_upper = upper_to_carrier['driver_teeth'] / upper_to_carrier['driven_teeth']
    carrier_ratio_to_barrel = lower_ratio_to_barrel * carrier_ratio_to_upper
    required_roles = [
        'spring_barrel_output',
        'lower_transfer_pinion',
        'vertical_lift_shaft',
        'upper_transfer_pinion',
        'carrier',
        'orbit_escape_pinion',
        'escape_wheel',
        'pallet_fork',
        'balance_wheel',
    ]
    present_roles = role.get('roles', {})
    missing = [name for name in required_roles if name not in present_roles]
    checks = [
        {'name': 'required motion roles exist in role manifest', 'status': 'pass' if not missing else 'fail', 'missing_roles': missing},
        {'name': 'barrel to lower transfer ratio is closed', 'status': 'pass' if lower_ratio_to_barrel == 2 else 'fail', 'ratio': lower_ratio_to_barrel},
        {'name': 'upper transfer to carrier ratio is closed', 'status': 'pass' if round(carrier_ratio_to_upper, 6) == 0.3 else 'fail', 'ratio': carrier_ratio_to_upper},
        {'name': 'barrel to carrier ratio is closed through vertical shaft', 'status': 'pass' if round(carrier_ratio_to_barrel, 6) == 0.6 else 'fail', 'ratio': carrier_ratio_to_barrel},
    ]
    status = 'pass' if all(check['status'] == 'pass' for check in checks) else 'fail'
    report = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'generation_id': role.get('generation_id'),
        'status': status,
        'type': 'fallback_transform_motion_contract_before_sampled_geometry_audit',
        'motion_story': [
            {'from': 'spring_barrel_output', 'to': 'lower_transfer_pinion', 'ratio_to_parent': lower_ratio_to_barrel},
            {'from': 'lower_transfer_pinion', 'to': 'vertical_lift_shaft', 'ratio_to_parent': 1.0},
            {'from': 'vertical_lift_shaft', 'to': 'upper_transfer_pinion', 'ratio_to_parent': 1.0},
            {'from': 'upper_transfer_pinion', 'to': 'carrier', 'ratio_to_parent': carrier_ratio_to_upper},
            {'from': 'carrier', 'to': 'orbit_escape_pinion', 'relative_ratio_in_carrier': -4.0},
            {'from': 'orbit_escape_pinion', 'to': 'escape_wheel', 'ratio_to_parent': 1.0},
            {'from': 'escape_wheel', 'to': 'pallet_fork', 'motion': 'eccentric_pin_slot_display'},
            {'from': 'pallet_fork', 'to': 'balance_wheel', 'motion': 'pallet_output_pin_display'},
        ],
        'sampled_driver_angles_deg': list(range(0, 360, 15)),
        'strict_language': 'fallback motion contract only; sampled geometry/contact/visibility audits are still required before completion',
        'checks': checks,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())

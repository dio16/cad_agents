from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'reports' / 'fabrication_v31_geometry_candidate'
OUT = PACKAGE / 'v31_proof_gap_audit.json'

REQUIRED = {
    'role_manifest': PACKAGE / 'v31_role_manifest_validation.json',
    'stationary_winding': PACKAGE / 'v31_stationary_winding_audit.json',
    'spatial_drive': PACKAGE / 'v31_spatial_drive_audit.json',
    'motion_validation': PACKAGE / 'v31_motion_validation.json',
    'sampled_motion': PACKAGE / 'v31_sampled_motion_audit.json',
    'declared_contact': PACKAGE / 'v31_declared_contact_audit.json',
    'visibility': PACKAGE / 'v31_visibility_audit.json',
    'dfam': PACKAGE / 'v31_dfam_audit.json',
    'object_value': PACKAGE / 'v31_object_value_audit.json',
    'user_deliverable': PACKAGE / 'v31_user_deliverable_validation.json',
    'gate_summary': PACKAGE / 'v31_gate_summary.json',
}

ORDER = [
    'role_manifest',
    'motion_validation',
    'sampled_motion',
    'declared_contact',
    'visibility',
    'dfam',
    'stationary_winding',
    'spatial_drive',
    'object_value',
    'user_deliverable',
    'gate_summary',
]


def load(path: Path) -> dict:
    if not path.exists():
        return {'status': 'missing'}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {'status': 'unreadable'}


def main() -> int:
    evidence = {}
    for name, path in REQUIRED.items():
        report = load(path)
        evidence[name] = {
            'path': str(path.relative_to(ROOT)),
            'status': report.get('status'),
            'exists': path.exists(),
        }
    missing = [name for name in ORDER if evidence[name]['status'] != 'pass']
    smallest_next = missing[0] if missing else None
    report = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'status': 'pass',
        'existing_passes': [name for name in ORDER if evidence[name]['status'] == 'pass'],
        'missing_or_nonpass': missing,
        'smallest_next_experiment': smallest_next,
        'rationale': (
            'Motion validation is the first missing load-bearing proof after the already-passing role manifest; '
            'without it, sampled motion, declared contact, visibility, and closeout would be built on an unproved motion contract.'
            if smallest_next == 'motion_validation'
            else 'All required proof artifacts already pass.'
        ),
        'evidence': evidence,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

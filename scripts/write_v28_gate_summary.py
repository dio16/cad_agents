from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifests' / 'tourbillon_v28_mechanism_contract.json'
PACKAGE = ROOT / 'reports' / 'fabrication_v28_mechanism_package'
OUT = PACKAGE / 'v28_gate_summary.json'
VISIBLE_MOVING_ROLES = {
    'carrier',
    'orbit_escape_pinion',
    'hand_input_pinion',
    'escape_wheel',
    'pallet_fork',
    'balance_wheel',
}
EXPECTED_CHAIN = [
    ('hand_input_pinion', 'carrier'),
    ('carrier', 'orbit_escape_pinion'),
    ('orbit_escape_pinion', 'escape_wheel'),
    ('escape_wheel', 'pallet_fork'),
    ('pallet_fork', 'balance_wheel'),
]
REQUIRED_BLOCKED_CLAIMS = {
    'watch-grade escapement',
    'regulating balance',
    'self-sustaining oscillation',
    'lock/drop/impulse verified',
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {'status': 'missing', 'path': str(path)}
    return json.loads(path.read_text(encoding='utf-8'))


def parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value)


def add(checks: list[dict], name: str, passed: bool, **detail: object) -> None:
    checks.append({'name': name, 'status': 'pass' if passed else 'fail', **detail})


def main() -> int:
    manifest = load_json(MANIFEST)
    role_manifest = load_json(PACKAGE / 'v28_role_manifest.json')
    motion_validation = load_json(PACKAGE / 'v28_motion_validation.json')
    mechanical_truth = load_json(PACKAGE / 'v28_mechanical_truth_audit.json')
    sampled_motion = load_json(PACKAGE / 'v28_sampled_motion_audit.json')
    declared_contact = load_json(PACKAGE / 'v28_declared_contact_audit.json')
    visibility = load_json(PACKAGE / 'v28_visibility_audit.json')
    viewer_smoke = load_json(PACKAGE / 'v28_wsl_http_viewer_smoke.json')
    checks: list[dict] = []

    roles = role_manifest.get('roles', {})
    axis_complete_roles = sorted(
        role
        for role in VISIBLE_MOVING_ROLES
        if {
            'parent',
            'support',
            'motion',
            'axis',
        }.issubset(roles.get(role, {}))
        and {
            'name',
            'origin_mm',
            'direction',
            'frame',
        }.issubset(roles.get(role, {}).get('axis', {}))
    )
    add(
        checks,
        'role manifest names every visible moving role with parent/support/motion/axis metadata',
        role_manifest.get('status') == 'pass' and set(axis_complete_roles) == VISIBLE_MOVING_ROLES,
        source='reports/fabrication_v28_mechanism_package/v28_role_manifest.json',
        axis_complete_roles=axis_complete_roles,
    )
    add(
        checks,
        'fallback transform motion artifact is present',
        motion_validation.get('status') == 'pass',
        source='reports/fabrication_v28_mechanism_package/v28_motion_validation.json',
        motion_type=motion_validation.get('type'),
    )
    add(
        checks,
        'mechanical truth audit passes',
        mechanical_truth.get('status') == 'pass',
        source='reports/fabrication_v28_mechanism_package/v28_mechanical_truth_audit.json',
    )
    add(
        checks,
        'sampled motion audit passes',
        sampled_motion.get('status') == 'pass',
        source='reports/fabrication_v28_mechanism_package/v28_sampled_motion_audit.json',
        undeclared_collision_count=sampled_motion.get('undeclared_collision_count'),
    )
    add(
        checks,
        'declared contact audit passes',
        declared_contact.get('status') == 'pass',
        source='reports/fabrication_v28_mechanism_package/v28_declared_contact_audit.json',
    )
    contact_sheet = Path(visibility.get('contact_sheet', ''))
    add(
        checks,
        'sampled local-geometry visibility evidence passes',
        visibility.get('status') == 'pass' and contact_sheet.exists() and contact_sheet.stat().st_size > 0,
        source='reports/fabrication_v28_mechanism_package/v28_visibility_audit.json',
        contact_sheet=str(contact_sheet),
        artifact_kind=visibility.get('artifact_kind'),
    )
    add(
        checks,
        'continuous local motion viewer smoke passes',
        viewer_smoke.get('status') == 'pass',
        source='reports/fabrication_v28_mechanism_package/v28_wsl_http_viewer_smoke.json',
    )

    actual_chain = [(item.get('from'), item.get('to')) for item in manifest.get('drive_chain', [])]
    blocked_claims = set(manifest.get('escapement_drive_model', {}).get('blocked_claims', []))
    blocked_claims.update(manifest.get('balance_drive_model', {}).get('blocked_claims', []))
    add(
        checks,
        'drive chain closes from hand input through pallet into balance',
        actual_chain == EXPECTED_CHAIN,
        source='manifests/tourbillon_v28_mechanism_contract.json',
        actual_chain=actual_chain,
    )
    add(
        checks,
        'claim boundary remains explicitly non-watch-grade',
        REQUIRED_BLOCKED_CLAIMS.issubset(blocked_claims)
        and 'non-regulating' in manifest.get('balance_drive_model', {}).get('claim', ''),
        source='manifests/tourbillon_v28_mechanism_contract.json',
        blocked_claims=sorted(blocked_claims),
    )

    manifest_ts = parse_ts(manifest.get('created_at'))
    report_paths = [
        PACKAGE / 'v28_role_manifest.json',
        PACKAGE / 'v28_motion_validation.json',
        PACKAGE / 'v28_mechanical_truth_audit.json',
        PACKAGE / 'v28_sampled_motion_audit.json',
        PACKAGE / 'v28_declared_contact_audit.json',
        PACKAGE / 'v28_visibility_audit.json',
        PACKAGE / 'v28_wsl_http_viewer_smoke.json',
    ]
    report_freshness = {
        str(path): parse_ts(load_json(path).get('created_at')) >= manifest_ts for path in report_paths
    }
    add(
        checks,
        'claim-transition reports are fresh against the current V28 manifest',
        all(report_freshness.values()),
        source='manifest/report timestamps',
        manifest_created_at=manifest.get('created_at'),
        report_freshness=report_freshness,
    )

    status = 'pass' if all(check['status'] == 'pass' for check in checks) else 'blocked'
    summary = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'completion_allowed': status == 'pass',
        'completion_wording': (
            'blocked: fresh independent V28 claim-transition evidence has not fully passed'
            if status != 'pass'
            else (
                'V28 object-level evidence passes for a mechanically driven tabletop tourbillon mechanism '
                'with a non-regulating demonstrative escapement; watch-grade escapement, regulating balance, '
                'self-sustaining oscillation, native CAD animation, and physical print evidence are not claimed'
            )
        ),
        'limitation': 'Local viewer evidence is continuous fallback transform motion, not native-CAD animation proof.',
        'checks': checks,
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return 0 if status == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())

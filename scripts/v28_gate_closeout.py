from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'reports' / 'fabrication_v28_mechanism_package'
OUT = PACKAGE / 'v28_gate_closeout.json'
RUNNER = ['bash', './run_cad_agent.sh', '--script']


def run_step(name: str, script: str) -> dict:
    command = [*RUNNER, script]
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        'name': name,
        'returncode': proc.returncode,
        'status': 'pass' if proc.returncode == 0 else 'fail',
        'command': command,
        'stdout_tail': proc.stdout[-4000:],
        'stderr_tail': proc.stderr[-4000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Regenerate the V28 package/evidence chain through the sanctioned Bash runner.'
    )
    parser.add_argument(
        '--evidence-only',
        action='store_true',
        help='Preserve the already-generated V28 package/manifest and refresh only claim-transition evidence.',
    )
    args = parser.parse_args()
    planned_steps = [
        ('create_v28_mechanism_package', 'scripts/create_v28_mechanism_package.py'),
        ('create_v28_motion_artifacts', 'scripts/create_v28_motion_artifacts.py'),
        ('v28_mechanical_truth_audit', 'scripts/v28_mechanical_truth_audit.py'),
        ('v28_sampled_motion_audit', 'scripts/v28_sampled_motion_audit.py'),
        ('v28_declared_contact_audit', 'scripts/v28_declared_contact_audit.py'),
        ('v28_visibility_audit', 'scripts/v28_visibility_audit.py'),
        ('v28_wsl_http_viewer_smoke', 'scripts/v28_wsl_http_viewer_smoke.py'),
        ('write_v28_gate_summary', 'scripts/write_v28_gate_summary.py'),
        ('create_v28_user_deliverable', 'scripts/create_v28_user_deliverable.py'),
        ('validate_v28_user_deliverable', 'scripts/validate_v28_user_deliverable.py'),
    ]
    if args.evidence_only:
        planned_steps = planned_steps[1:]
    steps = [run_step(name, script) for name, script in planned_steps]
    PACKAGE.mkdir(parents=True, exist_ok=True)
    report = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'status': 'pass' if all(step['status'] == 'pass' for step in steps) else 'blocked',
        'mode': 'evidence_only' if args.evidence_only else 'full_regeneration',
        'runner': RUNNER,
        'steps': steps,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'mode': report['mode'], 'report': str(OUT)}, indent=2))
    if report['status'] != 'pass':
        print(json.dumps(report, indent=2), file=sys.stderr)
    return 0 if report['status'] == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())

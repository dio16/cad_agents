from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / 'README.md'
README_JA = ROOT / 'README_JA.md'
CURRENT_DELIVERY = ROOT / 'deliverables' / 'current_delivery.json'
CURRENT_GOAL = ROOT / 'reports' / 'current_goal_summary.json'
OUT = ROOT / 'reports' / 'current_entrypoint_parity.json'


def load(path: Path) -> dict:
    if not path.exists():
        return {'status': 'missing'}
    return json.loads(path.read_text(encoding='utf-8'))


def add(checks: list[dict], name: str, ok: bool, **detail: object) -> None:
    checks.append({'name': name, 'status': 'pass' if ok else 'fail', **detail})


def main() -> int:
    readme = README.read_text(encoding='utf-8')
    readme_ja = README_JA.read_text(encoding='utf-8')
    delivery = load(CURRENT_DELIVERY)
    goal = load(CURRENT_GOAL)
    checks: list[dict] = []
    add(checks, 'README points to current delivery artifact', 'deliverables/current_delivery.json' in readme)
    add(checks, 'README points to current goal summary artifact', 'reports/current_goal_summary.json' in readme)
    add(checks, 'README_JA points to current delivery artifact', 'deliverables/current_delivery.json' in readme_ja)
    add(checks, 'README_JA points to current goal summary artifact', 'reports/current_goal_summary.json' in readme_ja)
    add(
        checks,
        'current goal summary and current delivery agree on package path',
        goal.get('deliverable_package_path') == delivery.get('deliverable_dir'),
        deliverable_package_path=goal.get('deliverable_package_path'),
        delivery_dir=delivery.get('deliverable_dir'),
    )
    add(
        checks,
        'current goal summary and current delivery agree on viewer entrypoint',
        goal.get('viewer_entrypoint') == delivery.get('viewer_entrypoint'),
        goal_viewer=goal.get('viewer_entrypoint'),
        delivery_viewer=delivery.get('viewer_entrypoint'),
    )
    status = 'pass' if all(check['status'] == 'pass' for check in checks) else 'fail'
    report = {'created_at': datetime.now(timezone.utc).isoformat(), 'status': status, 'checks': checks}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())

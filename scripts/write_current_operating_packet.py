from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / 'TASKS.md'
CURRENT_GOAL = ROOT / 'reports' / 'current_goal_summary.json'
CURRENT_DELIVERY = ROOT / 'deliverables' / 'current_delivery.json'
OUT_JSON = ROOT / 'reports' / 'current_operating_packet.json'
OUT_MD = ROOT / 'reports' / 'current_operating_packet.md'


def read_json(path: Path) -> dict:
    if not path.exists():
        return {'status': 'missing', 'path': str(path.relative_to(ROOT))}
    return json.loads(path.read_text(encoding='utf-8'))


def section_lines(text: str, name: str) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []
    inside = False
    for line in lines:
        if line == f'## {name}':
            inside = True
            continue
        if inside and line.startswith('## '):
            break
        if inside:
            out.append(line)
    return out


def bullets(lines: list[str], unchecked_only: bool = False) -> list[str]:
    vals = []
    for line in lines:
        if unchecked_only and line.startswith('- [ ] '):
            vals.append(line)
        elif not unchecked_only and line.startswith('- '):
            vals.append(line)
    return vals


def table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        if not line.startswith('|') or set(line.replace('|', '').replace('-', '').replace(' ', '')) == set():
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells and cells[0] not in {'Role', 'Order'}:
            rows.append(cells)
    return rows


def main() -> int:
    text = TASKS.read_text(encoding='utf-8')
    current_status = [line for line in section_lines(text, 'Current Status') if line.startswith('- ')]
    active_tasks = bullets(section_lines(text, 'Active Tasks'), unchecked_only=True)
    active_sidecars = table_rows(section_lines(text, 'Active Subagents'))
    inbox = bullets(section_lines(text, 'Emergent Tasks / Inbox'), unchecked_only=True)
    backlog = table_rows(section_lines(text, 'Conditional Mission Backlog'))
    next_queue = table_rows(section_lines(text, 'Next Task Queue'))
    current_goal = read_json(CURRENT_GOAL)
    current_delivery = read_json(CURRENT_DELIVERY)
    packet = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'status': 'pass',
        'current_status': current_status,
        'active_tasks': active_tasks,
        'active_sidecars': active_sidecars,
        'open_inbox': inbox,
        'conditional_backlog': backlog,
        'next_queue': next_queue,
        'current_goal_summary': {
            'status': current_goal.get('status'),
            'claim_tier': current_goal.get('claim_tier'),
            'completion_wording': current_goal.get('completion_wording'),
            'path': 'reports/current_goal_summary.json',
        },
        'current_delivery': {
            'version': current_delivery.get('version'),
            'deliverable_dir': current_delivery.get('deliverable_dir'),
            'viewer_entrypoint': current_delivery.get('viewer_entrypoint'),
            'path': 'deliverables/current_delivery.json',
        },
        'recommended_reads': [
            'GOAL.md',
            'AGENTS.md (authority / priority / turn-end / router sections)',
            'docs/codex_operating_alignment_ja.md for this operating-model loop',
        ],
    }
    OUT_JSON.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding='utf-8')

    md = [
        '# Current Operating Packet',
        '',
        f'- generated_at: `{packet["created_at"]}`',
        f'- current_goal_summary: `{packet["current_goal_summary"]["path"]}` → `{packet["current_goal_summary"]["status"]}`',
        f'- current_delivery: `{packet["current_delivery"]["path"]}` → `{packet["current_delivery"]["deliverable_dir"]}`',
        '',
        '## Current Status',
        *current_status,
        '',
        '## Open Active Tasks',
        *active_tasks,
        '',
        '## Open Inbox',
        *(inbox or ['- none']),
        '',
        '## Next Queue',
    ]
    for row in next_queue:
        if len(row) >= 3:
            md.append(f'- {row[0]}. {row[1]} — {row[2]}')
    md.extend([
        '',
        '## Read Next',
        '- `GOAL.md`',
        '- relevant `AGENTS.md` sections only',
        '- `docs/codex_operating_alignment_ja.md` for the current loop',
    ])
    OUT_MD.write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

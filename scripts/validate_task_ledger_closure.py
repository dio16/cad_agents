from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "TASKS.md"
OUT = ROOT / "reports" / "task_ledger_closure.json"

ACTIVE_RE = re.compile(r"^- \[ \] \[(P[1-3])\] (.+)$")
UNCHECKED_RE = re.compile(r"^- \[ \] (.+)$")


def section_lines(name: str) -> list[str]:
    lines = TASKS.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if line == f"## {name}":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            out.append(line)
    return out


def main() -> int:
    active = []
    for line in section_lines("Active Tasks"):
        match = ACTIVE_RE.match(line)
        if match:
            active.append({"priority": match.group(1), "task": match.group(2)})

    inbox = []
    for line in section_lines("Emergent Tasks / Inbox"):
        match = ACTIVE_RE.match(line)
        if match:
            inbox.append({"priority": match.group(1), "task": match.group(2)})
            continue
        unchecked = UNCHECKED_RE.match(line)
        if unchecked:
            task = unchecked.group(1)
            if task.startswith("[P4]"):
                continue
            inbox.append({"priority": "untriaged", "task": task})

    checks = [
        {
            "name": "no open active P1-P3 tasks",
            "status": "pass" if not active else "fail",
            "items": active,
        },
        {
            "name": "no open or untriaged emergent items",
            "status": "pass" if not inbox else "fail",
            "items": inbox,
        },
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "unresolved_mission_work": active + inbox,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

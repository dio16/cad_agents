from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "TASKS.md"
GOAL_STATE = ROOT / "reports" / "goal_state.json"
OUT = ROOT / "reports" / "goal_state_freshness.json"


def digest(path: Path) -> dict:
    raw = path.read_bytes()
    stat = path.stat()
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def main() -> int:
    current = digest(TASKS)
    stored = json.loads(GOAL_STATE.read_text(encoding="utf-8")).get("task_ledger", {})
    fresh = stored.get("sha256") == current["sha256"]
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if fresh else "fail",
        "stored_task_ledger": stored,
        "current_task_ledger": current,
        "checks": [
            {
                "name": "goal-state task-ledger digest matches current TASKS.md",
                "status": "pass" if fresh else "fail",
            }
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if fresh else 2


if __name__ == "__main__":
    raise SystemExit(main())

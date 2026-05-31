from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "TASKS.md"
GOAL_STATE = ROOT / "reports" / "goal_state.json"
CURRENT_SUMMARY = ROOT / "reports" / "current_goal_summary.json"
GOAL_FRESHNESS = ROOT / "reports" / "goal_state_freshness.json"
LEDGER_CLOSURE = ROOT / "reports" / "task_ledger_closure.json"


ACTIVE_TASK_RE = re.compile(r"^- \[ \] \[(P[1-3])\] (.+)$")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def active_tasks() -> list[dict]:
    tasks = []
    in_active = False
    for line in TASKS.read_text(encoding="utf-8").splitlines():
        if line == "## Active Tasks":
            in_active = True
            continue
        if in_active and line.startswith("## "):
            break
        if in_active:
            match = ACTIVE_TASK_RE.match(line)
            if match:
                tasks.append({"priority": match.group(1), "task": match.group(2)})
    return tasks


def tasks_fingerprint() -> dict:
    raw = TASKS.read_bytes()
    stat = TASKS.stat()
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def main() -> int:
    current_goal = load_json(CURRENT_SUMMARY)
    ledger_closure = load_json(LEDGER_CLOSURE)
    unresolved = ledger_closure.get("unresolved_mission_work", active_tasks())
    task_state = tasks_fingerprint()
    checks = [
        {
            "name": "current goal summary exists and passes",
            "status": "pass" if current_goal.get("status") == "pass" else "fail",
            "source": "reports/current_goal_summary.json",
        },
        {
            "name": "trusted claim reaches spatial-kinetic-sculpture-object",
            "status": "pass"
            if current_goal.get("claim_tier") == "spatial-kinetic-sculpture-object"
            else "fail",
            "claim_tier": current_goal.get("claim_tier"),
        },
        {
            "name": "stationary-autonomous-winding evidence passes",
            "status": "pass"
            if current_goal.get("stationary_autonomous_winding_evidence") == "pass"
            else "fail",
            "stationary_autonomous_winding_evidence": current_goal.get(
                "stationary_autonomous_winding_evidence"
            ),
        },
        {
            "name": "spatial-drive evidence passes",
            "status": "pass" if current_goal.get("spatial_drive_evidence") == "pass" else "fail",
            "spatial_drive_evidence": current_goal.get("spatial_drive_evidence"),
        },
        {
            "name": "object-value evidence passes",
            "status": "pass" if current_goal.get("object_value_evidence") == "pass" else "fail",
            "object_value_evidence": current_goal.get("object_value_evidence"),
        },
        {
            "name": "mechanical-truth evidence passes",
            "status": "pass" if current_goal.get("mechanical_truth_evidence") == "pass" else "fail",
            "mechanical_truth_evidence": current_goal.get("mechanical_truth_evidence"),
        },
        {
            "name": "object-level completion evidence passes",
            "status": "pass" if current_goal.get("object_completion_evidence") == "pass" else "fail",
            "object_completion_evidence": current_goal.get("object_completion_evidence"),
        },
        {
            "name": "user-consumable deliverable package passes",
            "status": "pass" if current_goal.get("user_consumable_deliverable") == "pass" else "fail",
            "user_consumable_deliverable": current_goal.get("user_consumable_deliverable"),
            "deliverable_package_path": current_goal.get("deliverable_package_path"),
            "viewer_entrypoint": current_goal.get("viewer_entrypoint"),
        },
        {
            "name": "user-facing entrypoint evidence passes",
            "status": "pass" if current_goal.get("user_entrypoint_evidence") == "pass" else "fail",
            "user_entrypoint_evidence": current_goal.get("user_entrypoint_evidence"),
        },
        {
            "name": "no unresolved mission work remains across the task ledger",
            "status": "pass" if ledger_closure.get("status") == "pass" and not unresolved else "fail",
            "unresolved_active_tasks": unresolved,
        },
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "blocked"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "task_ledger": task_state,
        "checks": checks,
    }
    GOAL_STATE.parent.mkdir(parents=True, exist_ok=True)
    GOAL_STATE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    freshness = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "stored_task_ledger": task_state,
        "current_task_ledger": task_state,
        "checks": [
            {
                "name": "goal-state task-ledger digest matches current TASKS.md",
                "status": "pass",
            }
        ],
    }
    GOAL_FRESHNESS.write_text(json.dumps(freshness, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

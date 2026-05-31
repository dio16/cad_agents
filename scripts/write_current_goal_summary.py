from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
OUT = ROOT / "reports" / "current_goal_summary.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, passed: bool, **detail: object) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", **detail})


def main() -> int:
    gate_summary = load_json(PACKAGE / "v30_gate_summary.json")
    viewer_smoke = load_json(PACKAGE / "v30_wsl_http_viewer_smoke.json")
    deliverable = load_json(PACKAGE / "v30_user_deliverable_validation.json")
    winding = load_json(PACKAGE / "v30_stationary_winding_audit.json")
    spatial = load_json(PACKAGE / "v30_spatial_drive_audit.json")
    object_value = load_json(PACKAGE / "v30_object_value_audit.json")
    mechanical_truth = load_json(PACKAGE / "v30_mechanical_truth_audit.json")
    completion_strength = load_json(PACKAGE / "v30_completion_strength_audit.json")
    coherence = load_json(ROOT / "reports" / "current_completion_coherence.json")
    checks: list[dict] = []
    add(checks, "V30 gate summary passes", gate_summary.get("status") == "pass")
    add(checks, "V30 viewer smoke passes", viewer_smoke.get("status") == "pass")
    add(checks, "V30 stationary winding passes", winding.get("status") == "pass")
    add(checks, "V30 spatial drive passes", spatial.get("status") == "pass")
    add(checks, "V30 object value passes", object_value.get("status") == "pass")
    add(checks, "V30 mechanical truth passes", mechanical_truth.get("status") == "pass")
    add(checks, "V30 user deliverable passes", deliverable.get("status") == "pass")
    add(checks, "V30 completion-strength audit passes", completion_strength.get("status") == "pass")
    add(checks, "same-generation completion coherence passes", coherence.get("status") == "pass")
    status = "pass" if all(check["status"] == "pass" for check in checks) else "blocked"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "goal_profile": "spatial-kinetic-sculpture-object",
        "claim_tier": "spatial-kinetic-sculpture-object" if status == "pass" else None,
        "stationary_autonomous_winding_evidence": "pass" if winding.get("status") == "pass" else "blocked",
        "spatial_drive_evidence": "pass" if spatial.get("status") == "pass" else "blocked",
        "object_value_evidence": "pass" if object_value.get("status") == "pass" else "blocked",
        "mechanical_truth_evidence": "pass" if mechanical_truth.get("status") == "pass" else "blocked",
        "object_completion_evidence": "pass" if gate_summary.get("status") == "pass" else "blocked",
        "user_consumable_deliverable": "pass" if deliverable.get("status") == "pass" else "blocked",
        "user_entrypoint_evidence": deliverable.get("user_entrypoint_evidence", "blocked"),
        "deliverable_package_path": deliverable.get("deliverable_dir"),
        "viewer_entrypoint": deliverable.get("viewer_entrypoint"),
        "printable_parts_dir": deliverable.get("printable_parts_dir"),
        "completion_allowed": status == "pass",
        "completion_wording": (
            "blocked: V30 evidence has not fully passed"
            if status != "pass"
            else (
                "local fabrication complete for a stationary-autonomous-winding spatial kinetic sculpture object "
                "with a geometry-backed lower power module, real vertical lift shaft, and an elevated demonstrative "
                "tourbillon core; watch-grade escapement, regulating balance, self-sustaining oscillation, "
                "native Onshape, and physical print evidence are not claimed"
            )
        ),
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

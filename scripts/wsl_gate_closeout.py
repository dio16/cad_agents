from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ["bash", "./run_cad_agent.sh", "--script"]


def run_step(name: str, args: list[str], allow_fail: bool = False) -> dict:
    proc = subprocess.run([*RUNNER, *args], cwd=ROOT, text=True, capture_output=True)
    result = {
        "name": name,
        "returncode": proc.returncode,
        "status": "pass" if proc.returncode == 0 else ("blocked" if allow_fail else "fail"),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "command": [*RUNNER, *args],
    }
    if proc.returncode != 0 and not allow_fail:
        print(json.dumps(result, indent=2), file=sys.stderr)
    return result


def main() -> int:
    steps = [
        run_step("wsl_runtime_proof", ["scripts/assert_wsl_runtime.py", "--local-only", "--write"]),
        run_step("generate_v27_connected_candidate", ["scripts/create_v27_connected_cadquery_package.py"]),
        run_step("generate_v27_motion_artifacts", ["scripts/create_v27_motion_artifacts.py"], allow_fail=True),
        run_step("v27_wsl_http_viewer_smoke", ["scripts/v27_wsl_http_viewer_smoke.py"], allow_fail=True),
        run_step("independent_v27_connected_audit", ["scripts/independent_v27_connected_audit.py"], allow_fail=True),
        run_step("v27_step_interference_audit", ["scripts/v27_step_interference_audit.py"], allow_fail=True),
        run_step("v27_mechanical_truth_audit", ["scripts/v27_mechanical_truth_audit.py"], allow_fail=True),
        run_step("v27_sampled_motion_audit", ["scripts/v27_sampled_motion_audit.py"], allow_fail=True),
        run_step("v27_declared_mesh_contact_audit", ["scripts/v27_declared_mesh_contact_audit.py"], allow_fail=True),
        run_step("v27_visibility_audit", ["scripts/v27_visibility_audit.py"], allow_fail=True),
        run_step("artifact_provenance", ["scripts/write_artifact_provenance.py"]),
        run_step("current_gate_summary", ["scripts/write_current_gate_summary.py"], allow_fail=True),
    ]
    report = {"status": "pass" if all(step["returncode"] == 0 for step in steps) else "blocked", "steps": steps}
    path = ROOT / "reports" / "wsl_gate_closeout.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(path)}, indent=2))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

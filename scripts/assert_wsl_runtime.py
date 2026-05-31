from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "reports" / "wsl_runtime_proof.json"
APPROVED_PREFIX = (ROOT / ".venv").as_posix()
APPROVED_PYTHON = (ROOT / ".venv/bin/python").as_posix()
CANONICAL_ROOT = Path("/home/diobrando/codex_wsl/cad_agent_framework").as_posix()
SANCTIONED_ENTRYPOINT = "run_cad_agent.sh"
SANCTIONED_RUNNER = f"{CANONICAL_ROOT}/{SANCTIONED_ENTRYPOINT}"
SANCTIONED_SHELL = "bash"


def is_wsl() -> bool:
    try:
        text = Path("/proc/version").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        text = ""
    return platform.system() == "Linux" and ("microsoft" in text or "wsl" in text)


def module_status(names: list[str]) -> dict[str, bool]:
    import importlib.util

    return {name: importlib.util.find_spec(name) is not None for name in names}


def runtime_report(local_only: bool) -> dict:
    modules = module_status(["cadquery", "OCP", "build123d", "trimesh", "numpy"])
    python_path = Path(sys.executable).as_posix()
    cwd = Path.cwd().resolve().as_posix()
    entrypoint = os.environ.get("CAD_AGENT_ENTRYPOINT", "")
    runner = os.environ.get("CAD_AGENT_RUNNER", "")
    shell = os.environ.get("CAD_AGENT_SHELL", "")
    runner_local_only = os.environ.get("CAD_AGENT_LOCAL_ONLY", "") == "1"
    effective_local_only = local_only or runner_local_only
    env = {
        "ONSHAPE_ACCESS_KEY": bool(os.environ.get("ONSHAPE_ACCESS_KEY")),
        "ONSHAPE_SECRET_KEY": bool(os.environ.get("ONSHAPE_SECRET_KEY")),
    }
    checks = [
        {"name": "platform is WSL Linux", "status": "pass" if is_wsl() else "fail"},
        {"name": "python executable is approved WSL CAD runtime", "status": "pass" if python_path.startswith(APPROVED_PREFIX) else "fail", "python": python_path},
        {"name": "cwd is canonical WSL repo root", "status": "pass" if cwd == CANONICAL_ROOT else "fail", "cwd": cwd, "canonical_root": CANONICAL_ROOT},
        {
            "name": "sanctioned Bash runner provenance is present",
            "status": "pass" if entrypoint == SANCTIONED_ENTRYPOINT and runner == SANCTIONED_RUNNER and shell == SANCTIONED_SHELL else "fail",
            "entrypoint": entrypoint,
            "runner": runner,
            "shell": shell,
            "expected_entrypoint": SANCTIONED_ENTRYPOINT,
            "expected_runner": SANCTIONED_RUNNER,
            "expected_shell": SANCTIONED_SHELL,
        },
        {"name": "CAD and mesh validation modules import", "status": "pass" if all(modules.values()) else "fail", "modules": modules},
        {
            "name": "runtime is UV-managed venv",
            "status": "pass" if os.environ.get("UV_PROJECT_ENVIRONMENT") or python_path.endswith("/.venv/bin/python") else "fail",
            "python": python_path,
        },
        {
            "name": "Onshape credentials present or explicitly waived",
            "status": "pass" if effective_local_only or all(env.values()) else "fail",
            "local_only": effective_local_only,
            "requested_local_only": local_only,
            "runner_local_only": runner_local_only,
            "env": env,
        },
    ]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
        "cwd": cwd,
        "platform": platform.platform(),
        "python": python_path,
        "approved_python_prefix": APPROVED_PREFIX,
        "approved_python": APPROVED_PYTHON,
        "canonical_root": CANONICAL_ROOT,
        "sanctioned_entrypoint": SANCTIONED_ENTRYPOINT,
        "sanctioned_runner": SANCTIONED_RUNNER,
        "sanctioned_shell": SANCTIONED_SHELL,
        "local_only": effective_local_only,
        "requested_local_only": local_only,
        "runner_local_only": runner_local_only,
        "checks": checks,
    }


def assert_wsl_runtime(local_only: bool = False, write: bool = False, output: Path = DEFAULT_OUT) -> dict:
    report = runtime_report(local_only=local_only)
    if write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if report["status"] != "pass":
        raise RuntimeError(json.dumps(report, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Assert canonical WSL CAD runtime")
    parser.add_argument("--local-only", action="store_true", help="Waive Onshape env vars for local-only validation/generation")
    parser.add_argument("--write", action="store_true", help="Write reports/wsl_runtime_proof.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = runtime_report(local_only=args.local_only)
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cad_agent.workflow import (
    completion_status,
    design_check,
    generate_motion_preview,
    hardware_context_audit,
    load_manifest,
    local_assembly_export,
    local_backend_status,
    local_fabrication_audit,
    local_pose_snapshots,
    motion_check,
    solid_interference_audit,
)

from scripts.assert_wsl_runtime import assert_wsl_runtime


def current_gate_summary_result() -> dict:
    path = Path(__file__).resolve().parent / "reports" / "current_gate_summary.json"
    if not path.exists():
        return {
            "status": "blocked",
            "completion_allowed": False,
            "completion_wording": "blocked: reports/current_gate_summary.json is missing",
            "source": str(path),
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": "pass" if data.get("completion_allowed") else "blocked",
        "completion_allowed": bool(data.get("completion_allowed")),
        "completion_wording": data.get("completion_wording", "blocked: invalid current gate summary"),
        "source": str(path),
        "checks": data.get("checks", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Local-first agentic CAD workflow CLI")
    parser.add_argument("--manifest", required=True, type=Path)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("completion-status")
    sub.add_parser("local-backend-status")
    sub.add_parser("local-fabrication-audit")
    sub.add_parser("local-assembly-export")
    sub.add_parser("local-completion-status")
    local_pose = sub.add_parser("local-pose-snapshots")
    local_pose.add_argument("--angles", nargs="*", type=float, default=[0.0, 45.0, 90.0, 135.0, 180.0])
    sub.add_parser("check")
    sub.add_parser("motion")
    solid = sub.add_parser("solid-audit")
    solid.add_argument("--sample-step-deg", type=float, default=45.0)
    hw = sub.add_parser("hardware-context-audit")
    hw.add_argument("--sample-step-deg", type=float, default=90.0)
    preview = sub.add_parser("motion-preview")
    preview.add_argument("--output", type=Path)

    args = parser.parse_args()
    assert_wsl_runtime(local_only=True, write=True)

    if args.cmd == "status":
        result = load_manifest(args.manifest)
    elif args.cmd == "completion-status":
        result = current_gate_summary_result()
    elif args.cmd == "local-backend-status":
        result = local_backend_status(args.manifest)
    elif args.cmd == "local-fabrication-audit":
        result = local_fabrication_audit(args.manifest)
    elif args.cmd == "local-assembly-export":
        result = local_assembly_export(args.manifest)
    elif args.cmd == "local-completion-status":
        result = current_gate_summary_result()
    elif args.cmd == "local-pose-snapshots":
        result = local_pose_snapshots(args.manifest, angles=args.angles)
    elif args.cmd == "check":
        result = design_check(args.manifest)
    elif args.cmd == "motion":
        result = motion_check(args.manifest)
    elif args.cmd == "solid-audit":
        result = solid_interference_audit(args.manifest, sample_step_deg=args.sample_step_deg)
    elif args.cmd == "hardware-context-audit":
        result = hardware_context_audit(args.manifest, sample_step_deg=args.sample_step_deg)
    elif args.cmd == "motion-preview":
        result = generate_motion_preview(args.manifest, args.output)
    else:
        raise AssertionError(args.cmd)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

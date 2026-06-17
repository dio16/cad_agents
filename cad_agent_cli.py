from __future__ import annotations

import argparse
import json
from pathlib import Path

from cad_agent.phase2_pilot import DEFAULT_PHASE2_OUTPUT_DIR, run_phase2_pilot
from cad_agent.platform_poc import DEFAULT_OUTPUT_DIR, DEFAULT_REPORT_DIR, contract_report, run_golden_pipeline
from scripts.validate_platform_contracts import validate


MAINTAINED_COMMANDS = [
    "status",
    "validate-docs",
    "phase1-contract-test",
    "phase1-golden-pipeline",
    "phase2-pilot-run",
    "serve",
    "sbom",
    "provenance",
]


def _print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def _status_report() -> dict[str, object]:
    return {
        "status": "aligned",
        "source_proposal": "docs/Origen/Design_document_for_a_machine_design_platform.md",
        "maintained_commands": MAINTAINED_COMMANDS,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI machine design platform repository checks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Print repository alignment status")
    status_parser.set_defaults(func=_status_report)

    validate_docs_parser = subparsers.add_parser("validate-docs", help="Validate maintained docs and scripts")
    validate_docs_parser.set_defaults(func=validate)

    subparsers.add_parser("phase1-contract-test", help="Run Phase 1 schema and AST contract tests")

    phase1_golden_parser = subparsers.add_parser("phase1-golden-pipeline", help="Run the single-part Phase 1 PoC pipeline")
    phase1_golden_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)

    phase2_pilot_parser = subparsers.add_parser("phase2-pilot-run", help="Run Phase 2 pilot integration checks")
    phase2_pilot_parser.add_argument("--output-dir", type=Path, default=DEFAULT_PHASE2_OUTPUT_DIR)

    serve_parser = subparsers.add_parser("serve", help="Run the local API server skeleton")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--dry-run", action="store_true", help="Instantiate the handler and exit without serving")
    serve_parser.set_defaults(func=None)

    sbom_parser = subparsers.add_parser("sbom", help="Generate a deterministic SPDX-lite SBOM from pyproject.toml and uv.lock")
    sbom_parser.add_argument("--project", type=Path, default=Path("pyproject.toml"))
    sbom_parser.add_argument("--lock", type=Path, default=Path("uv.lock"))
    sbom_parser.add_argument("--output", type=Path)
    sbom_parser.add_argument("--created-at", default="1970-01-01T00:00:00Z")
    sbom_parser.set_defaults(func=None)

    provenance_parser = subparsers.add_parser("provenance", help="Generate a deterministic SLSA-like provenance stub")
    provenance_parser.add_argument("--project", type=Path, default=Path("pyproject.toml"))
    provenance_parser.add_argument("--lock", type=Path, default=Path("uv.lock"))
    provenance_parser.add_argument("--output", type=Path)
    provenance_parser.add_argument("--created-at")
    provenance_parser.set_defaults(func=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        _print_json(args.func())
        return 0
    if args.command == "validate-docs":
        code, report = args.func()
        _print_json(report)
        return code
    if args.command == "phase1-contract-test":
        report = contract_report()
        report_path = DEFAULT_REPORT_DIR / "phase1_contract_test.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        _print_json(report)
        return 0 if report["status"] == "pass" else 2
    if args.command == "phase1-golden-pipeline":
        report = run_golden_pipeline(args.output_dir)
        _print_json(report)
        return 0 if report["status"] == "pass" else 2
    if args.command == "phase2-pilot-run":
        report = run_phase2_pilot(args.output_dir)
        _print_json(report)
        return 0 if report["status"] == "pass" else 2
    if args.command == "serve":
        from cad_agent.api_server import instantiate_handler, run_server

        if args.dry_run:
            instantiate_handler()
            print(f"API server dry-run OK: configured for {args.host}:{args.port}")
            return 0
        run_server(args.host, args.port)
        return 0
    if args.command == "sbom":
        from scripts.generate_sbom import build_sbom, write_json

        write_json(build_sbom(args.project, args.lock, args.created_at), args.output)
        return 0
    if args.command == "provenance":
        from scripts.provenance import build_provenance, write_json

        write_json(build_provenance(args.project, args.lock, args.created_at), args.output)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

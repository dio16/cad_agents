from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CREATED_AT = "1970-01-01T00:00:00Z"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_project_name(project_path: Path) -> tuple[str, str]:
    import tomllib

    with project_path.open("rb") as file:
        project = tomllib.load(file)
    project_meta = project.get("project", {})
    return str(project_meta.get("name", project_path.stem)), str(project_meta.get("version", "0.0.0"))


def _created_at(value: str | None) -> str:
    if value:
        return value
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch:
        return datetime.fromtimestamp(int(source_date_epoch), timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return DEFAULT_CREATED_AT


def build_provenance(
    project_path: Path = Path("pyproject.toml"),
    lock_path: Path = Path("uv.lock"),
    created_at: str | None = None,
) -> dict[str, Any]:
    project_name, project_version = _load_project_name(project_path)
    pyproject_hash = _sha256_file(project_path)
    lock_hash = _sha256_file(lock_path)
    subject_digest = hashlib.sha256(f"{pyproject_hash}:{lock_hash}".encode("utf-8")).hexdigest()
    timestamp = _created_at(created_at)

    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {
                "name": project_name,
                "digest": {
                    "sha256": subject_digest,
                },
            }
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "local://cad-agent-framework/skeleton",
                "externalParameters": {
                    "repository": "cad_agent_framework",
                    "commands": {
                        "illustrative": True,
                        "items": [
                            "bash ./run_cad_agent.sh status",
                            "bash ./run_cad_agent.sh validate-docs",
                            "bash ./run_cad_agent.sh phase1-contract-test",
                            "bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/...",
                            "bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/...",
                            "uv run pytest -q",
                        ],
                    },
                },
                "internalParameters": {
                    "project": str(project_path),
                    "lockfile": str(lock_path),
                    "pyproject_sha256": pyproject_hash,
                    "uv_lock_sha256": lock_hash,
                },
            },
            "runDetails": {
                "builder": {
                    "id": "local://cad-agent-framework/scripts/provenance.py",
                },
                "metadata": {
                    "invocationId": f"{project_name}-{project_version}-provenance",
                    "startedOn": timestamp,
                    "finishedOn": timestamp,
                    "stub": True,
                    "note": "Declarative skeleton only; not a signed SLSA attestation.",
                },
                "byproducts": [
                    {
                        "name": "pyproject.toml",
                        "digest": {"sha256": pyproject_hash},
                    },
                    {
                        "name": "uv.lock",
                        "digest": {"sha256": lock_hash},
                    },
                ],
            },
        },
    }


def write_json(data: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(rendered)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic SLSA-like provenance stub")
    parser.add_argument("--project", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--lock", type=Path, default=Path("uv.lock"))
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--created-at",
        default=None,
        help="Creation timestamp. Defaults to SOURCE_DATE_EPOCH if set, otherwise 1970-01-01T00:00:00Z.",
    )
    args = parser.parse_args(argv)
    created_at = args.created_at or _created_at(None)
    write_json(build_provenance(args.project, args.lock, created_at), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

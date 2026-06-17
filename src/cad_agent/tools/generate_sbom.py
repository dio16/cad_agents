from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

DEFAULT_CREATED_AT = "1970-01-01T00:00:00Z"
SPDX_VERSION = "SPDX-2.3"
SPDX_DATA_LICENSE = "CC0-1.0"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_project(project_path: Path) -> dict[str, Any]:
    with project_path.open("rb") as file:
        return tomllib.load(file)


def _load_lock(lock_path: Path) -> dict[str, Any]:
    with lock_path.open("rb") as file:
        return tomllib.load(file)


def _source_name(source: dict[str, Any]) -> str:
    if "editable" in source:
        return "editable"
    if "registry" in source:
        return "pypi"
    return "unknown"


def _hash_value(digest: dict[str, Any] | str) -> str | None:
    if isinstance(digest, str):
        return digest
    if "sha256" in digest:
        return f"sha256:{digest['sha256']}"
    for algorithm, value in sorted(digest.items()):
        return f"{algorithm}:{value}"
    return None


def _artifact_hashes(package: dict[str, Any]) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    sdist_hash = _hash_value(package.get("sdist", {}).get("hash", {}))
    if sdist_hash:
        artifacts.append({"type": "sdist", "algorithm": "sha256", "value": sdist_hash})
    for wheel in package.get("wheels", []):
        wheel_hash = _hash_value(wheel.get("hash", {}))
        if wheel_hash:
            artifacts.append({"type": "wheel", "algorithm": "sha256", "value": wheel_hash})
    return artifacts


def _package_to_sbom(package: dict[str, Any]) -> dict[str, Any]:
    name = str(package["name"])
    version = str(package["version"])
    dependencies = sorted(str(dependency["name"]) for dependency in package.get("dependencies", []))
    return {
        "name": name,
        "version": version,
        "purl": f"pkg:pypi/{name}@{version}",
        "source": _source_name(package.get("source", {})),
        "dependencies": dependencies,
        "artifact_hashes": _artifact_hashes(package),
    }


def _direct_dependencies(project: dict[str, Any]) -> list[str]:
    return sorted(str(dependency) for dependency in project.get("project", {}).get("dependencies", []))


def _optional_dependencies(project: dict[str, Any]) -> dict[str, list[str]]:
    optional = project.get("project", {}).get("optional-dependencies", {})
    return {
        str(extra): sorted(str(dependency) for dependency in dependencies)
        for extra, dependencies in sorted(optional.items())
    }


def _document_namespace(project_name: str, project_version: str, pyproject_path: Path, lock_path: Path) -> str:
    combined = f"{_sha256_file(pyproject_path)}:{_sha256_file(lock_path)}"
    return f"https://cad-agent-framework.local/spdx-like/{project_name}-{project_version}-{_sha256_text(combined)[:16]}"


def build_sbom(project_path: Path = Path("pyproject.toml"), lock_path: Path = Path("uv.lock"), created_at: str | None = None) -> dict[str, Any]:
    project = _load_project(project_path)
    lock = _load_lock(lock_path)
    project_meta = project.get("project", {})
    project_name = str(project_meta.get("name", project_path.stem))
    project_version = str(project_meta.get("version", "0.0.0"))
    packages = [_package_to_sbom(package) for package in lock.get("package", [])]
    packages.sort(key=lambda package: (package["name"], package["version"]))

    return {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": SPDX_DATA_LICENSE,
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{project_name}-spdx-like-sbom",
        "documentNamespace": _document_namespace(project_name, project_version, project_path, lock_path),
        "creationInfo": {
            "created": created_at or DEFAULT_CREATED_AT,
            "creators": ["Tool: scripts/generate_sbom.py"],
            "comment": "Deterministic local SPDX-like SBOM stub generated from pyproject.toml and uv.lock without network access.",
        },
        "project": {
            "name": project_name,
            "version": project_version,
            "requires_python": project_meta.get("requires-python"),
            "dependencies": _direct_dependencies(project),
            "optional_dependencies": _optional_dependencies(project),
        },
        "packages": packages,
    }


def write_json(data: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(rendered)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic SPDX-like SBOM from pyproject.toml and uv.lock")
    parser.add_argument("--project", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--lock", type=Path, default=Path("uv.lock"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--created-at", default=DEFAULT_CREATED_AT, help="Creation timestamp; defaults to 1970-01-01T00:00:00Z for deterministic output")
    args = parser.parse_args(argv)

    sbom = build_sbom(args.project, args.lock, args.created_at)
    write_json(sbom, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    Path("docs/Origen/Design_document_for_a_machine_design_platform.md"),
    Path("README.md"),
    Path("README_JA.md"),
    Path("GOAL.md"),
    Path("SPEC.md"),
    Path("TASKS.md"),
    Path("AGENTS.md"),
    Path("docs/architecture_ja.md"),
    Path("docs/api_contracts_ja.md"),
    Path("docs/validation_security_ja.md"),
    Path("docs/operations_ja.md"),
]

REQUIRED_TERMS = [
    "Requirement JSON",
    "Specification JSON",
    "Parametric DSL",
    "Validation Report",
    "traceability",
]

STALE_TERMS = [
    "tourbillon_v",
    "トゥールビヨン",
    "Onshape",
    "PowerShell",
]

STALE_COMMAND_TERMS = [
    "--manifest",
    "solid-audit",
    "geometry-audit",
]


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""


def add(checks: list[Check], name: str, condition: bool, detail: str = "") -> None:
    checks.append(Check(name=name, status="pass" if condition else "fail", detail=detail))


def read(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def validate() -> tuple[int, dict[str, object]]:
    checks: list[Check] = []

    for path in REQUIRED_DOCS:
        add(checks, f"required document exists: {path}", (ROOT / path).exists())

    maintained_docs = [p for p in REQUIRED_DOCS if (ROOT / p).exists()]
    combined = "\n".join(read(p) for p in maintained_docs)

    for term in REQUIRED_TERMS:
        add(checks, f"canonical term present: {term}", term in combined)

    for path in [Path("README.md"), Path("README_JA.md"), Path("SPEC.md"), Path("docs/api_contracts_ja.md")]:
        text = read(path)
        add(checks, f"{path} points to Origen proposal", "docs/Origen/Design_document_for_a_machine_design_platform.md" in text)

    current_docs = [p for p in (ROOT / "docs").glob("*.md")]
    current_docs += [ROOT / n for n in ["README.md", "README_JA.md", "GOAL.md", "SPEC.md", "TASKS.md"]]
    for path in current_docs:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        for term in STALE_TERMS:
            # README_JA may mention old docs were removed once; that is allowed.
            allowed = rel in {Path("README.md"), Path("README_JA.md")} and "旧" in text and "削除" in text
            add(checks, f"no stale term '{term}' in {rel}", allowed or term not in text)
        for command_term in STALE_COMMAND_TERMS:
            add(checks, f"no stale command term '{command_term}' in {rel}", command_term not in text)

    runner = read(Path("run_cad_agent.sh"))
    add(checks, "runner exposes validate-docs", "validate-docs" in runner)
    add(checks, "runner avoids legacy manifest contract", "--manifest" not in runner)

    status = "pass" if all(c.status == "pass" for c in checks) else "fail"
    report = {
        "status": status,
        "checks": [c.__dict__ for c in checks],
    }
    return (0 if status == "pass" else 2), report


def main() -> int:
    code, report = validate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

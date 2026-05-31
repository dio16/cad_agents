from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DOCS = [
    ROOT / "AGENTS.md",
    ROOT / "GOAL.md",
    ROOT / "README.md",
    ROOT / "README_JA.md",
    ROOT / "docs" / "mechanical_design_workflow_ja.md",
    ROOT / "docs" / "skill_governance_ja.md",
    ROOT / "docs" / "design_rule_register_ja.md",
]

FORBIDDEN_ACTIVE_PATTERNS = [
    (
        "powershell code fence",
        re.compile(r"```powershell", re.IGNORECASE),
    ),
    (
        "PowerShell launcher guidance",
        re.compile(r"(?:run_cad_agent\.ps1|pwsh\s+|powershell\s+.+run_cad_agent)", re.IGNORECASE),
    ),
    (
        "cmd.exe launcher guidance",
        re.compile(r"\bcmd\.exe\b", re.IGNORECASE),
    ),
    (
        "direct cad_agent_cli.py invocation",
        re.compile(r"(?<!run_cad_agent\.sh\s)(?:python(?:3)?|/[^\\s]+/python)\s+cad_agent_cli\.py\b"),
    ),
]

NEGATIVE_POLICY_MARKERS = (
    "do not use",
    "must not use",
    "not valid",
    "disabled legacy",
    "使いません",
    "禁止",
)


def is_negative_policy_line(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in NEGATIVE_POLICY_MARKERS)


def scan() -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in ACTIVE_DOCS:
        if not path.exists():
            findings.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "line": 0,
                    "pattern": "missing active doc",
                    "text": "",
                }
            )
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if is_negative_policy_line(line):
                continue
            for label, pattern in FORBIDDEN_ACTIVE_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        {
                            "path": str(path.relative_to(ROOT)),
                            "line": line_no,
                            "pattern": label,
                            "text": line.strip(),
                        }
                    )
    return findings


def main() -> int:
    findings = scan()
    if not findings:
        print("bash-only active-doc check: pass")
        return 0

    print("bash-only active-doc check: fail")
    for finding in findings:
        print(
            f"{finding['path']}:{finding['line']}: {finding['pattern']}: "
            f"{finding['text']}"
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

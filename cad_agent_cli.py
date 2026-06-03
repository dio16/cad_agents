from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="AI machine design platform repository checks")
    parser.add_argument("cmd", choices=["status", "validate-docs"])
    args = parser.parse_args()
    if args.cmd == "status":
        print(json.dumps({
            "status": "aligned",
            "source_proposal": "docs/Origen/Design_document_for_a_machine_design_platform.md",
            "maintained_commands": ["status", "validate-docs"],
        }, ensure_ascii=False, indent=2))
        return 0
    return subprocess.call(["python3", str(ROOT / "scripts" / "validate_platform_contracts.py")])


if __name__ == "__main__":
    raise SystemExit(main())

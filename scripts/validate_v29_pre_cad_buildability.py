from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_pre_cad_buildability_contract.json"
OUT = ROOT / "reports" / "v29_pre_cad_buildability_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    contract = load(CONTRACT)
    roles = contract["moving_roles"]
    checks: list[dict] = []
    add(checks, "all moving roles declare support", all(role.get("support") for role in roles))
    add(checks, "all moving roles declare retention", all(role.get("retention") for role in roles))
    add(checks, "all moving roles declare print orientation", all(role.get("print_orientation") for role in roles))
    add(checks, "all moving roles declare tool access", all(role.get("tool_access") for role in roles))
    add(checks, "minimum wall is printable", contract["dfam_assumptions"]["minimum_wall_mm"] >= 2.0)
    add(checks, "shaft radial clearance is printable", contract["dfam_assumptions"]["shaft_radial_clearance_mm"] >= 0.15)
    add(checks, "assembly sequence is explicit", len(contract["assembly_sequence"]) >= 5)
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_contract": str(CONTRACT),
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

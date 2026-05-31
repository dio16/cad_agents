from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_component_selection_contract.json"
OUT = ROOT / "reports" / "v29_component_selection_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    contract = load(CONTRACT)
    parts = {part["role"]: part for part in contract["purchased_parts"]}
    checks: list[dict] = []
    add(checks, "all source contracts exist", all((ROOT / p).exists() for p in contract["source_contracts"]))
    add(checks, "motor family is dimensionally checked", parts["winding_motor"]["selection_level"] == "dimensionally checked")
    add(checks, "spring family is dimensionally checked", parts["energy_storage"]["selection_level"] == "dimensionally checked")
    add(checks, "motor family fits chamber", parts["winding_motor"]["envelope_mm"][0] <= 25 and parts["winding_motor"]["envelope_mm"][2] <= 50)
    add(checks, "spring family fits barrel", parts["energy_storage"]["envelope_mm"][0] <= 36)
    add(checks, "printed / purchased BOM separation is explicit", contract["bom_policy"]["printed_and_purchased_parts_separate"] is True)
    add(checks, "fabrication claim still requires reference solids", contract["bom_policy"]["reference_solids_required_before_fabrication_claim"] is True)
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

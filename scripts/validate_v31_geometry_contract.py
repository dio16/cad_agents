from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v31_geometry_contract.json"
FEASIBILITY = ROOT / "reports" / "v31_selected_design_feasibility_validation.json"
OUT = ROOT / "reports" / "v31_geometry_contract_validation.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    feasibility = json.loads(FEASIBILITY.read_text(encoding="utf-8")) if FEASIBILITY.exists() else {"status": "missing"}
    checks = [
        {"name": "source contracts exist", "status": "pass" if all((ROOT / path).exists() for path in contract["source_contracts"]) else "fail"},
        {"name": "selected-design feasibility passes", "status": "pass" if feasibility.get("status") == "pass" else "fail"},
        {"name": "required artifacts include full-system proof bundle", "status": "pass" if {"role_manifest", "sampled_motion_audit", "declared_contact_audit", "visibility_contact_sheet", "dfam_audit"}.issubset(contract["required_artifacts"]) else "fail"},
        {"name": "geometry contract preserves winding and spatial assumptions", "status": "pass" if {"ratchet winding wheel", "spring barrel", "reverse-flow protection", "overwind protection", "vertical lift shaft"}.issubset(contract["must_preserve"]) else "fail"},
    ]
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "claim": "geometry-ready" if status == "pass" else "not geometry-ready",
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

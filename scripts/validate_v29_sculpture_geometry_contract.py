from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_sculpture_geometry_contract.json"
OUT = ROOT / "reports" / "v29_sculpture_geometry_contract_validation.json"
FEASIBILITY = ROOT / "reports" / "v29_selected_design_feasibility_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    contract = load(CONTRACT)
    feasibility = load(FEASIBILITY)
    checks: list[dict] = []
    add(checks, "all source contracts exist", all((ROOT / p).exists() for p in contract["source_contracts"]))
    add(checks, "three frame families exist", set(contract["frames"]) == {"base_frame", "riser_frame", "carrier_frame_30deg"})
    add(checks, "all three motion layers are declared", set(contract["role_groups"]) == {"slow_macro", "medium_transfer", "fast_fine"})
    add(checks, "printable part set is nontrivial", len(contract["printable_parts"]) >= 10)
    add(checks, "artifact set includes viewer and BOM", {"motion_viewer", "printed_bom", "purchased_bom"}.issubset(contract["required_artifacts"]))
    add(checks, "geometry cannot bypass feasibility closure", "selected_design_feasibility_closure_pass" in contract["required_gates"])
    add(
        checks,
        "fresh selected-design feasibility artifact passes",
        feasibility.get("status") == "pass",
        source=str(FEASIBILITY),
        feasibility_claim=feasibility.get("claim"),
    )
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_contract": str(CONTRACT),
        "source_feasibility_artifact": str(FEASIBILITY),
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

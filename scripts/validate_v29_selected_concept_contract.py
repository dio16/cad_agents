from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v29_selected_concept_contract.json"
OUT = ROOT / "reports" / "v29_selected_concept_contract_validation.json"
EXPECTED_CHAIN = [
    "low_voltage_motor",
    "visible_winding_drum",
    "spring_barrel",
    "horizontal_transfer_shaft",
    "bevel_riser",
    "canted_carrier_drive",
    "tourbillon_carrier",
    "orbit_escape_pinion",
    "escape_wheel",
    "pallet_fork",
    "balance_wheel",
]


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    actual_chain = [data["drive_chain"][0]["from"]] + [edge["to"] for edge in data["drive_chain"]]
    checks = {
        "goal_profile": data.get("goal_profile") == "spatial-kinetic-sculpture-object",
        "selected_concept": data.get("concept_id") == "A_powered_winding_drum_bevel_riser_canted_cage",
        "stationary_autonomous_semantics": "stationary-autonomous-winding" in data.get("claim", ""),
        "drive_chain_continuity": actual_chain == EXPECTED_CHAIN,
        "autonomous_winding_architecture": {
            "input",
            "visible_energy_role",
            "storage",
            "output",
            "claim_boundary",
        }.issubset(data.get("autonomous_winding_architecture", {})),
        "spatial_drive_transition_count": len(data.get("spatial_drive_transitions", [])) >= 2,
        "value_brief_complete": {
            "far_view",
            "mid_view",
            "near_view",
            "layered_rhythm",
            "avoid",
        }.issubset(data.get("value_brief", {})),
        "pre_cad_gate_set_present": len(data.get("required_pre_cad_gates", [])) >= 10,
    }
    status = "pass" if all(checks.values()) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": checks,
        "actual_chain": actual_chain,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

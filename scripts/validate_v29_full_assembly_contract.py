from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_full_assembly_contract.json"
OUT = ROOT / "reports" / "v29_full_assembly_contract_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    contract = load(CONTRACT)
    checks: list[dict] = []

    source_contracts = [ROOT / path for path in contract["source_contracts"]]
    add(
        checks,
        "all source contracts exist",
        all(path.exists() for path in source_contracts),
        source_contracts=[str(path) for path in source_contracts],
    )
    add(
        checks,
        "claim uses stationary-autonomous-winding semantics",
        "stationary-autonomous-winding" in contract["claim"],
        claim=contract["claim"],
    )
    modules = {module["name"]: module for module in contract["modules"]}
    add(
        checks,
        "all three selected V29 modules are present",
        set(modules) == {"autonomous_power_module", "spatial_riser", "canted_cage_display"},
        modules=sorted(modules),
    )
    add(
        checks,
        "motion hierarchy is complete",
        {module["motion_class"] for module in modules.values()}
        == {"slow_macro", "medium_transfer", "fast_fine"},
        motion_classes=sorted({module["motion_class"] for module in modules.values()}),
    )
    add(
        checks,
        "drive chain closes from motor to balance",
        contract["drive_chain"][0] == "low_voltage_motor"
        and contract["drive_chain"][-1] == "balance_wheel"
        and len(contract["drive_chain"]) >= 10,
        drive_chain=contract["drive_chain"],
    )
    transitions = {item["name"]: item for item in contract["spatial_transitions"]}
    add(
        checks,
        "low-plane to elevated-plane transition is explicit",
        transitions.get("low_plane_to_elevated_plane", {}).get("from_height_mm") == 20
        and transitions.get("low_plane_to_elevated_plane", {}).get("to_height_mm") == 62,
        transition=transitions.get("low_plane_to_elevated_plane"),
    )
    add(
        checks,
        "elevated display remains canted",
        transitions.get("elevated_plane_to_canted_display", {}).get("to_axis") == "canted_30_deg",
        transition=transitions.get("elevated_plane_to_canted_display"),
    )
    evidence = set(contract["required_future_evidence"])
    add(
        checks,
        "future evidence set matches raised goal",
        {
            "stationary_autonomous_winding_evidence",
            "spatial_drive_evidence",
            "object_value_evidence",
            "mechanical_truth_evidence",
            "deliverable_package_evidence",
        }.issubset(evidence),
        required_future_evidence=sorted(evidence),
    )
    add(
        checks,
        "pre-geometry gates include interface control",
        "cross_module_integration_pass" in contract["required_pre_geometry_gates"]
        and "kinematic_dimension_contract_pass" in contract["required_pre_geometry_gates"],
        required_pre_geometry_gates=contract["required_pre_geometry_gates"],
    )
    add(
        checks,
        "selected-design feasibility closure is encoded before geometry",
        contract["status"] == "mechanically_viable_pre_cad_after_selected_design_feasibility"
        and "selected_design_feasibility_closure_pass" in contract["required_pre_geometry_gates"],
        contract_status=contract["status"],
        required_pre_geometry_gates=contract["required_pre_geometry_gates"],
    )

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

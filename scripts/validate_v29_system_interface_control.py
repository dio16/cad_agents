from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_system_interface_control_contract.json"
OUT = ROOT / "reports" / "v29_system_interface_control_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def overlap(a: list[float], b: list[float]) -> float:
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def main() -> int:
    contract = load(CONTRACT)
    modules = {module["name"]: module for module in contract["modules"]}
    checks: list[dict] = []

    add(checks, "exactly three modules are interface-controlled", len(modules) == 3, modules=sorted(modules))
    for interface in contract["interfaces"]:
        src = modules[interface["from_module"]]
        dst = modules[interface["to_module"]]
        out = next((item for item in src["outputs"] if item["name"] == interface["from_output"]), None)
        inp = next((item for item in dst["inputs"] if item["name"] == interface["to_input"]), None)
        add(checks, f"{interface['from_module']} output exists", out is not None)
        add(checks, f"{interface['to_module']} input exists", inp is not None)
        required = interface["required_match"]
        if interface["handoff_type"] == "coaxial_shaft":
            add(
                checks,
                f"{interface['from_module']} -> {interface['to_module']} axis matches",
                out is not None
                and inp is not None
                and out.get("axis") == required["axis"]
                and inp.get("axis") == required["axis"]
                and out.get("centerline_height_mm") == required["centerline_height_mm"]
                and inp.get("centerline_height_mm") == required["centerline_height_mm"],
                required=required,
                actual_output=out,
                actual_input=inp,
            )
        else:
            add(
                checks,
                f"{interface['from_module']} -> {interface['to_module']} transition is declared",
                out is not None
                and inp is not None
                and out.get("centerline_height_mm") == required["centerline_height_mm"]
                and inp.get("centerline_height_mm") == required["centerline_height_mm"]
                and inp.get("axis") == "z_to_canted",
                required=required,
                actual_output=out,
                actual_input=inp,
            )

    pair_names = [
        ("autonomous_power_module", "spatial_riser"),
        ("spatial_riser", "canted_cage_display"),
        ("autonomous_power_module", "canted_cage_display"),
    ]
    for left_name, right_name in pair_names:
        left = modules[left_name]["reserved_envelope_mm"]
        right = modules[right_name]["reserved_envelope_mm"]
        volume = (
            overlap(left["x"], right["x"])
            * overlap(left["y"], right["y"])
            * overlap(left["z"], right["z"])
        )
        declared_adjacent_pair = {left_name, right_name} in [
            {"autonomous_power_module", "spatial_riser"},
            {"spatial_riser", "canted_cage_display"},
        ]
        add(
            checks,
            f"{left_name} / {right_name} envelope overlap is controlled",
            volume == 0.0 or declared_adjacent_pair,
            overlap_volume_mm3=volume,
            declared_adjacent_pair=declared_adjacent_pair,
        )

    add(
        checks,
        "all modules carry hero-view occlusion budgets",
        all(module.get("hero_view_occlusion_budget") for module in modules.values()),
    )
    add(checks, "assembly order has four executable stages", len(contract["assembly_order"]) == 4)

    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_contract": str(CONTRACT),
        "checks": checks,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

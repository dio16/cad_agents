from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_risky_subsystems_contract.json"
SUMMARY = ROOT / "reports" / "fabrication_v29_risky_subsystems" / "v29_risky_subsystems_summary.json"
OUT = ROOT / "reports" / "fabrication_v29_risky_subsystems" / "v29_risky_subsystems_review.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    contract = load(CONTRACT)
    summary = load(SUMMARY)
    checks: list[dict] = []

    expected = {module["name"]: module for module in contract["modules"]}
    actual_modules = {module["name"]: module for module in summary["modules"]}
    declared_roles = summary.get("module_roles", {})
    parameters = summary.get("parameters", {})
    contact_sheet = Path(summary.get("contact_sheet", ""))

    add(
        checks,
        "summary references risky-subsystems contract",
        summary.get("source_contract") == "manifests/tourbillon_v29_risky_subsystems_contract.json",
        source_contract=summary.get("source_contract"),
    )
    add(
        checks,
        "all contracted modules exist",
        set(actual_modules) == set(expected),
        expected=sorted(expected),
        actual=sorted(actual_modules),
    )
    for name, spec in expected.items():
        actual = actual_modules.get(name, {})
        add(
            checks,
            f"{name} STEP exists",
            Path(actual.get("step", "")).exists(),
            path=actual.get("step"),
        )
        add(
            checks,
            f"{name} STL exists",
            Path(actual.get("stl", "")).exists(),
            path=actual.get("stl"),
        )
        add(
            checks,
            f"{name} declares required roles",
            set(declared_roles.get(name, [])) == set(spec["required_roles"]),
            expected=spec["required_roles"],
            actual=declared_roles.get(name, []),
        )
    add(
        checks,
        "power module summary passes macro-motion envelope check",
        summary.get("checks", {}).get("power_module_has_macro_motion_envelope") is True,
    )
    add(
        checks,
        "spatial riser summary passes axis-height check",
        summary.get("checks", {}).get("spatial_riser_changes_axis_height") is True
        and parameters.get("spatial_riser_axis_lift_mm", 0) >= 40,
        spatial_riser_axis_lift_mm=parameters.get("spatial_riser_axis_lift_mm"),
    )
    add(
        checks,
        "canted cage summary preserves bounded tilt concept",
        summary.get("checks", {}).get("canted_cage_has_tilted_envelope") is True
        and parameters.get("canted_cage_tilt_deg") == 30,
        canted_cage_tilt_deg=parameters.get("canted_cage_tilt_deg"),
    )
    add(
        checks,
        "review contact sheet exists",
        contact_sheet.exists() and contact_sheet.stat().st_size > 0,
        path=str(contact_sheet),
    )

    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "claim": contract["claim"],
        "source_contract": str(CONTRACT),
        "source_summary": str(SUMMARY),
        "what_this_proves": [
            "the selected V29 concept has explicit concept-only modules for the three expensive unknowns",
            "each module has declared learning objectives, roles, and local artifacts",
            "the package is now contract-traceable instead of being shape-only",
        ],
        "what_this_does_not_prove": [
            "full sculpture geometry",
            "full drive ratios or torque reserve",
            "fabrication completion",
            "final object-value pass",
        ],
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

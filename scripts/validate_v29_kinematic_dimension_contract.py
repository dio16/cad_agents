from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v29_kinematic_dimension_contract.json"
OUT = ROOT / "reports" / "v29_kinematic_dimension_contract_validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    contract = load(CONTRACT)
    checks: list[dict] = []

    add(
        checks,
        "source full assembly contract exists",
        (ROOT / contract["source_contract"]).exists(),
        source_contract=contract["source_contract"],
    )
    add(
        checks,
        "default backlash is printable-positive",
        contract["gear_assumptions"]["printed_backlash_target_mm"] >= 0.2,
        printed_backlash_target_mm=contract["gear_assumptions"]["printed_backlash_target_mm"],
    )
    for mesh in contract["gear_meshes"]:
        module = mesh["module_mm"]
        driver_pitch = mesh["driver"]["teeth"] * module / 2.0
        driven_pitch = mesh["driven"]["teeth"] * module / 2.0
        expected_center = (
            driver_pitch + driven_pitch if mesh["type"] != "internal" else abs(driver_pitch - driven_pitch)
        )
        add(
            checks,
            f"{mesh['name']} pitch radii match module",
            abs(driver_pitch - mesh["pitch_radii_mm"]["driver"]) < 1e-9
            and abs(driven_pitch - mesh["pitch_radii_mm"]["driven"]) < 1e-9,
            expected_driver_pitch_mm=driver_pitch,
            expected_driven_pitch_mm=driven_pitch,
            declared=mesh["pitch_radii_mm"],
        )
        add(
            checks,
            f"{mesh['name']} center distance matches gear type",
            abs(expected_center - mesh["center_distance_mm"]) < 1e-9,
            expected_center_distance_mm=expected_center,
            declared_center_distance_mm=mesh["center_distance_mm"],
        )
        if mesh["type"] == "internal":
            expected_ratio = -expected_center / driven_pitch
            add(
                checks,
                f"{mesh['name']} internal rolling spin ratio matches geometry",
                abs(expected_ratio - mesh["absolute_spin_ratio_vs_carrier"]) < 1e-9,
                expected_ratio=expected_ratio,
                declared_ratio=mesh["absolute_spin_ratio_vs_carrier"],
            )
        else:
            expected_speed_ratio = -mesh["driver"]["teeth"] / mesh["driven"]["teeth"]
            expected_torque_ratio = mesh["driven"]["teeth"] / mesh["driver"]["teeth"]
            add(
                checks,
                f"{mesh['name']} speed ratio matches tooth counts",
                abs(expected_speed_ratio - mesh["speed_ratio_driven_over_driver"]) < 1e-9,
                expected_ratio=expected_speed_ratio,
                declared_ratio=mesh["speed_ratio_driven_over_driver"],
            )
            add(
                checks,
                f"{mesh['name']} ideal torque ratio matches tooth counts",
                abs(expected_torque_ratio - mesh["ideal_torque_ratio_driven_over_driver"]) < 1e-9,
                expected_ratio=expected_torque_ratio,
                declared_ratio=mesh["ideal_torque_ratio_driven_over_driver"],
            )

    add(
        checks,
        "all primary loaded shafts are two-point supported",
        all(item["support_style"] == "two_point" for item in contract["shaft_supports"]),
    )
    add(
        checks,
        "external pinions avoid unshifted undercut risk",
        all(
            mesh["driver"]["teeth"] >= contract["gear_assumptions"]["minimum_unshifted_external_pinion_teeth"]
            and mesh["driven"]["teeth"] >= contract["gear_assumptions"]["minimum_unshifted_external_pinion_teeth"]
            for mesh in contract["gear_meshes"]
            if mesh["type"] in {"external", "bevel_equivalent"}
        ),
        minimum_unshifted_external_pinion_teeth=contract["gear_assumptions"][
            "minimum_unshifted_external_pinion_teeth"
        ],
    )
    add(
        checks,
        "shaft radial clearances remain printable",
        all(item["clearance_radial_mm"] >= 0.15 for item in contract["shaft_supports"]),
        clearances=[item["clearance_radial_mm"] for item in contract["shaft_supports"]],
    )
    add(
        checks,
        "support spans are bounded for concept stage",
        all(15 <= item["support_span_mm"] <= 45 for item in contract["shaft_supports"]),
        support_spans=[item["support_span_mm"] for item in contract["shaft_supports"]],
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

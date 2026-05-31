from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
SUMMARY = PACKAGE / "v30_package_summary.json"
V28_CORE = ROOT / "reports" / "fabrication_v28_mechanism_package" / "v28_mechanical_truth_audit.json"
V28_MOTION = ROOT / "reports" / "fabrication_v28_mechanism_package" / "v28_sampled_motion_audit.json"
ROLE_MANIFEST = PACKAGE / "v30_role_manifest.json"
SAMPLED_MOTION = PACKAGE / "v30_sampled_motion_audit.json"
DECLARED_CONTACT = PACKAGE / "v30_declared_contact_audit.json"
OUT = PACKAGE / "v30_mechanical_truth_audit.json"


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    v28_core = json.loads(V28_CORE.read_text(encoding="utf-8"))
    v28_motion = json.loads(V28_MOTION.read_text(encoding="utf-8"))
    role_manifest = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8")) if ROLE_MANIFEST.exists() else {"status": "missing"}
    sampled_motion = json.loads(SAMPLED_MOTION.read_text(encoding="utf-8")) if SAMPLED_MOTION.exists() else {"status": "missing"}
    declared_contact = json.loads(DECLARED_CONTACT.read_text(encoding="utf-8")) if DECLARED_CONTACT.exists() else {"status": "missing"}
    parts = {item["name"]: item for item in summary["parts"]}
    checks: list[dict] = []
    required = {
        "10_motor_pinion_18t_v30",
        "11_visible_winding_drum_gear_108t_v30",
        "12_spring_barrel_output_gear_36t_v30",
        "13_lower_transfer_pinion_18t_v30",
        "14_upper_transfer_pinion_18t_v30",
        "16_motor_output_shaft_ref_v30",
        "17_winding_arbor_ref_v30",
        "18_vertical_lift_shaft_ref_v30",
        "02_lower_support_bridge_v30",
    }
    add(checks, "all new force-path solids exist", required.issubset(parts), missing=sorted(required - set(parts)))
    motor_y, wind_y, lift_y = -135.9, -85.5, -58.5
    add(checks, "motor-to-winding center distance closes", math.isclose(abs(wind_y - motor_y), 50.4, abs_tol=1e-6), actual=abs(wind_y - motor_y))
    add(checks, "barrel-to-lower-transfer center distance closes", math.isclose(abs(wind_y - lift_y), 27.0, abs_tol=1e-6), actual=abs(wind_y - lift_y))
    add(checks, "upper-transfer-to-carrier center distance closes", math.isclose(abs(lift_y - 0.0), 58.5, abs_tol=1e-6), actual=abs(lift_y))
    add(
        checks,
        "vertical lift shaft bridges lower and upper transmission planes",
        parts["18_vertical_lift_shaft_ref_v30"]["bbox_mm"]["z"][0] <= 8
        and parts["18_vertical_lift_shaft_ref_v30"]["bbox_mm"]["z"][1] >= 68,
        bbox=parts["18_vertical_lift_shaft_ref_v30"]["bbox_mm"],
    )
    add(
        checks,
        "support bridge spans the winding and lift axes",
        parts["02_lower_support_bridge_v30"]["bbox_mm"]["y"][0] <= wind_y
        and parts["02_lower_support_bridge_v30"]["bbox_mm"]["y"][1] >= lift_y,
        bbox=parts["02_lower_support_bridge_v30"]["bbox_mm"],
    )
    add(
        checks,
        "validated V28 core is reused as elevated mechanism",
        {
            "04_fixed_internal_ring_72t_v30",
            "05_rotating_carrier_drive_gear_v30",
            "06_orbit_escape_pinion_18t_v30",
            "07_balance_wheel_v30",
            "08_escape_wheel_15t_v30",
            "09_pallet_fork_bridge_v30",
        }.issubset(parts),
    )
    add(checks, "source V28 core mechanical truth passes", v28_core.get("status") == "pass")
    add(checks, "source V28 sampled motion passes", v28_motion.get("status") == "pass")
    add(checks, "V30 role manifest passes for the full system", role_manifest.get("status") == "pass")
    add(checks, "V30 sampled motion passes for the full system", sampled_motion.get("status") == "pass")
    add(checks, "V30 declared-contact audit passes for the full system", declared_contact.get("status") == "pass")
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": summary.get("generation_id"),
        "status": status,
        "checks": checks,
        "completion_allowed": status == "pass",
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

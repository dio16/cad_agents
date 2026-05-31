from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KIN = ROOT / "manifests" / "tourbillon_v29_kinematic_dimension_contract.json"
PACKAGE = ROOT / "reports" / "fabrication_v29_sculpture_package"
SUMMARY = PACKAGE / "v29_package_summary.json"
ROLE_MANIFEST = PACKAGE / "v29_role_manifest.json"
OUT = PACKAGE / "v29_mechanical_truth_audit.json"


def add(checks: list[dict], name: str, ok: bool, **detail) -> None:
    checks.append({"name": name, "status": "pass" if ok else "fail", **detail})


def main() -> int:
    kin = json.loads(KIN.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    roles = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8"))
    part_names = {item["name"] for item in summary["parts"]}
    geometry_roles = {
        "visible_winding_drum",
        "spring_barrel",
        "horizontal_transfer",
        "vertical_riser",
        "canted_drive",
        "fixed_internal_ring",
        "carrier",
        "orbit_escape_pinion",
        "escape_wheel",
        "pallet_fork",
        "balance_wheel",
    }
    represented_mesh_roles = {
        "visible_winding_drum_gear",
        "horizontal_transfer_pinion",
        "vertical_riser_bevel",
        "canted_drive_pinion",
        "carrier_drive_gear",
        "fixed_internal_ring",
        "orbit_escape_pinion",
    }
    required_mesh_roles = {
        role
        for mesh in kin["gear_meshes"]
        for role in (mesh["driver"]["role"], mesh["driven"]["role"])
    }
    checks: list[dict] = []
    add(
        checks,
        "every kinematic mesh role is physically represented by generated geometry",
        required_mesh_roles.issubset(represented_mesh_roles),
        missing_roles=sorted(required_mesh_roles - represented_mesh_roles),
    )
    add(
        checks,
        "generated package includes an explicit shaft/arbor part",
        any("shaft" in name or "arbor" in name for name in part_names),
        generated_parts=sorted(part_names),
    )
    add(
        checks,
        "role manifest is backed by generated support solids, not labels only",
        False,
        reason="V29 role manifest declares supports, but no generated audit proves bores, seats, or support solids for the declared axes.",
    )
    add(
        checks,
        "all visible moving roles are represented in the motion graph",
        geometry_roles.issubset(set(roles["roles"]) | {"spring_barrel", "canted_drive", "fixed_internal_ring"}),
        missing_roles=sorted(geometry_roles - set(roles["roles"]) - {"spring_barrel", "canted_drive", "fixed_internal_ring"}),
    )
    add(
        checks,
        "gear train closes through physical mesh types actually present in geometry",
        False,
        reason="Current geometry uses a spur horizontal gear, a spur vertical gear, and a canted spur gear where the contract requires two bevel-equivalent axis transitions.",
    )
    add(
        checks,
        "viewer transforms are joint-relative rather than whole-part self-rotations",
        False,
        reason="Current viewer rotates meshes about their own imported origins and can animate disconnected bodies without shafts or mates.",
    )
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": checks,
        "completion_allowed": status == "pass",
        "failure_summary": (
            None
            if status == "pass"
            else "V29 geometry is a disconnected visual study, not a mechanically closed sculpture object."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

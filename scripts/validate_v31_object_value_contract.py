from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manifests" / "tourbillon_v31_object_value_contract.json"
OUT = ROOT / "reports" / "v31_object_value_contract_validation.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    checks = [
        {"name": "hero view role set is nontrivial", "status": "pass" if len(contract["hero_view_required_roles"]) >= 8 else "fail"},
        {"name": "three motion layers are declared", "status": "pass" if set(contract["motion_layers"]) == {"slow_macro", "medium_transfer", "fast_fine"} else "fail"},
        {"name": "occlusion budget is explicit", "status": "pass" if 0 < contract["occlusion_budget_percent_max"] <= 35 else "fail"},
        {"name": "spatial value is explicit", "status": "pass" if "lower-to-upper" in contract["spatial_value"] else "fail"},
    ]
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "status": status, "checks": checks}
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v29_sculpture_package"
SUMMARY = PACKAGE / "v29_package_summary.json"
OUT = PACKAGE / "v29_spatial_drive_audit.json"


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    by_name = {item["name"]: item for item in summary["parts"]}
    riser = by_name["05_spatial_riser_bridge_v29"]["bbox_mm"]
    carrier = by_name["09_canted_carrier_frame_v29"]["bbox_mm"]
    checks = [
        {
            "name": "riser spans materially different heights",
            "status": "pass" if riser["z"][1] - riser["z"][0] >= 40 else "fail",
            "z_span_mm": round(riser["z"][1] - riser["z"][0], 3),
        },
        {
            "name": "carrier occupies a canted elevated frame",
            "status": "pass" if carrier["z"][1] - carrier["z"][0] > 30 else "fail",
            "z_span_mm": round(carrier["z"][1] - carrier["z"][0], 3),
        },
        {
            "name": "both riser and canted-drive parts exist",
            "status": "pass"
            if {"05_spatial_riser_bridge_v29", "06_vertical_riser_gear_v29", "07_canted_carrier_drive_gear_v29"}.issubset(by_name)
            else "fail",
        },
    ]
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

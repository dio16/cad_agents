from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
SUMMARY = SOURCE / "v30_package_summary.json"
OUT = ROOT / "deliverables" / "tourbillon_v30"
CURRENT = ROOT / "deliverables" / "current_delivery.json"


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "stl").mkdir(parents=True)
    for stl in (SOURCE / "stl").glob("*.stl"):
        shutil.copy2(stl, OUT / "stl" / stl.name)
    shutil.copy2(SOURCE / "v30_3d_cad_motion_viewer.html", OUT / "viewer.html")
    if (SOURCE / "v30_wsl_http_viewer_smoke.png").exists():
        shutil.copy2(SOURCE / "v30_wsl_http_viewer_smoke.png", OUT / "preview.png")
    for name in ("printed_parts.csv", "purchased_parts.csv", "assembly_sequence.csv"):
        shutil.copy2(SOURCE / name, OUT / name)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": summary.get("generation_id"),
        "version": "V30",
        "viewer_entrypoint": "viewer.html",
        "preview_files": ["preview.png"],
        "printable_parts_dir": "stl",
        "printed_parts": "printed_parts.csv",
        "purchased_parts": "purchased_parts.csv",
        "assembly_sequence": "assembly_sequence.csv",
    }
    (OUT / "package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text("# Tourbillon V30 Deliverable\n\n- Viewer: `viewer.html`\n- Printable STL: `stl/`\n", encoding="utf-8")
    CURRENT.write_text(json.dumps({"version": "V30", "generation_id": summary.get("generation_id"), "deliverable_dir": "deliverables/tourbillon_v30", "viewer_entrypoint": "deliverables/tourbillon_v30/viewer.html"}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "pass", "deliverable": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

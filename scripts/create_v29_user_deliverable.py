from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports" / "fabrication_v29_sculpture_package"
OUT = ROOT / "deliverables" / "tourbillon_v29"
CURRENT = ROOT / "deliverables" / "current_delivery.json"


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "stl").mkdir(parents=True)
    for stl in (SOURCE / "stl").glob("*.stl"):
        shutil.copy2(stl, OUT / "stl" / stl.name)
    shutil.copy2(SOURCE / "v29_3d_cad_motion_viewer.html", OUT / "viewer.html")
    shutil.copy2(SOURCE / "v29_visibility_contact_sheet.png", OUT / "preview_contact_sheet.png")
    for name in ("printed_parts.csv", "purchased_parts.csv", "assembly_sequence.csv"):
        shutil.copy2(SOURCE / name, OUT / name)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "V29",
        "viewer_entrypoint": "viewer.html",
        "preview_files": ["preview_contact_sheet.png"],
        "printable_parts_dir": "stl",
        "printed_parts": "printed_parts.csv",
        "purchased_parts": "purchased_parts.csv",
        "assembly_sequence": "assembly_sequence.csv",
    }
    (OUT / "package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text(
        "# Tourbillon V29 Deliverable\n\n- Viewer: `viewer.html`\n- Printable STL: `stl/`\n- Preview: `preview_contact_sheet.png`\n",
        encoding="utf-8",
    )
    current = {
        "version": "V29",
        "deliverable_dir": "deliverables/tourbillon_v29",
        "viewer_entrypoint": "deliverables/tourbillon_v29/viewer.html",
    }
    CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
    print(json.dumps({"status": "pass", "deliverable": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

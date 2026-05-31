from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "tourbillon_v28"
REPORT = ROOT / "reports" / "fabrication_v28_mechanism_package" / "v28_user_deliverable_validation.json"
SOURCE_MANIFEST = ROOT / "manifests" / "tourbillon_v28_mechanism_contract.json"
CURRENT_DELIVERY = ROOT / "deliverables" / "current_delivery.json"
EXPECTED_STL_COUNT = 9


def add(checks: list[dict], name: str, passed: bool, **detail: object) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", **detail})


def main() -> int:
    manifest_path = OUT / "package_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    current_delivery = json.loads(CURRENT_DELIVERY.read_text(encoding="utf-8")) if CURRENT_DELIVERY.exists() else {}
    stls = sorted((OUT / "stl").glob("*.stl"))
    checks: list[dict] = []
    add(checks, "deliverable directory exists", OUT.exists(), path=str(OUT))
    add(checks, "package manifest exists", manifest_path.exists(), path=str(manifest_path))
    add(checks, "viewer entrypoint exists", (OUT / "viewer.html").exists(), path="viewer.html")
    add(checks, "preview image exists", (OUT / "preview.png").exists(), path="preview.png")
    add(checks, "contact-sheet preview exists", (OUT / "preview_contact_sheet.png").exists(), path="preview_contact_sheet.png")
    add(checks, "printed parts csv exists", (OUT / "printed_parts.csv").exists(), path="printed_parts.csv")
    add(checks, "purchased parts csv exists", (OUT / "purchased_parts.csv").exists(), path="purchased_parts.csv")
    add(checks, "assembly sequence exists", (OUT / "assembly_sequence.csv").exists(), path="assembly_sequence.csv")
    add(checks, "japanese readme exists", (OUT / "README_JA.md").exists(), path="README_JA.md")
    add(checks, "stable current-delivery index exists", (ROOT / "deliverables" / "README.md").exists(), path="deliverables/README.md")
    add(checks, "stable current-delivery japanese index exists", (ROOT / "deliverables" / "README_JA.md").exists(), path="deliverables/README_JA.md")
    add(checks, "machine current-delivery index exists", CURRENT_DELIVERY.exists(), path="deliverables/current_delivery.json")
    add(checks, "expected printable STL count", len(stls) == EXPECTED_STL_COUNT, count=len(stls), expected=EXPECTED_STL_COUNT)
    add(checks, "all STL files non-empty", bool(stls) and all(path.stat().st_size > 0 for path in stls), files=[path.name for path in stls])
    add(checks, "print bundle zip exists", (OUT / "tourbillon_v28_print_bundle.zip").exists(), path="tourbillon_v28_print_bundle.zip")
    add(checks, "manifest uses relative viewer path", manifest.get("viewer_entrypoint") == "viewer.html", viewer_entrypoint=manifest.get("viewer_entrypoint"))
    add(checks, "manifest declares printable parts dir", manifest.get("printable_parts_dir") == "stl", printable_parts_dir=manifest.get("printable_parts_dir"))
    add(checks, "manifest object class is goal-level mechanism", manifest.get("object_class") == "mechanically-driven-tabletop-mechanism", object_class=manifest.get("object_class"))
    add(checks, "manifest generation matches source", manifest.get("generation_id") == source_manifest.get("generation_id"), package_generation_id=manifest.get("generation_id"), source_generation_id=source_manifest.get("generation_id"))
    add(checks, "current-delivery index points at current package", current_delivery.get("package_path") == "deliverables/tourbillon_v28", package_path=current_delivery.get("package_path"))
    add(checks, "current-delivery index points at current viewer", current_delivery.get("viewer_entrypoint") == "deliverables/tourbillon_v28/viewer.html", viewer_entrypoint=current_delivery.get("viewer_entrypoint"))
    add(checks, "current-delivery index matches source generation", current_delivery.get("generation_id") == source_manifest.get("generation_id"), current_generation_id=current_delivery.get("generation_id"), source_generation_id=source_manifest.get("generation_id"))
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    entrypoint_names = {
        "stable current-delivery index exists",
        "stable current-delivery japanese index exists",
        "machine current-delivery index exists",
        "current-delivery index points at current package",
        "current-delivery index points at current viewer",
        "current-delivery index matches source generation",
    }
    entrypoint_checks = [check for check in checks if check["name"] in entrypoint_names]
    entrypoint_evidence = "pass" if all(check["status"] == "pass" for check in entrypoint_checks) else "blocked"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "deliverable_dir": "deliverables/tourbillon_v28",
        "viewer_entrypoint": "deliverables/tourbillon_v28/viewer.html",
        "printable_parts_dir": "deliverables/tourbillon_v28/stl",
        "entrypoint_evidence": entrypoint_evidence,
        "checks": checks,
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

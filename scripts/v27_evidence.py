from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v27_connected_contract.json"
DERIVED_COMPLETION_FILES = [
    ROOT / "reports" / "fabrication_v27_connected_package" / "v27_role_manifest.json",
    ROOT / "reports" / "fabrication_v27_connected_package" / "v27_motion_validation.json",
    ROOT / "reports" / "fabrication_v27_connected_package" / "v27_3d_cad_motion_viewer.html",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def artifact_set_sha256() -> str:
    data = manifest()
    h = hashlib.sha256()
    for item in sorted(data["parts"], key=lambda row: row["name"]):
        for key in ("step", "stl"):
            path = Path(item[key])
            h.update(path.name.encode("utf-8"))
            h.update(sha256(path).encode("ascii"))
    return h.hexdigest()


def evidence_fields() -> dict:
    data = manifest()
    return {
        "generation_id": data.get("generation_id"),
        "input_manifest_sha256": sha256(MANIFEST),
        "input_artifact_set_sha256": artifact_set_sha256(),
    }


def derived_completion_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): sha256(path)
        for path in DERIVED_COMPLETION_FILES
        if path.exists()
    }

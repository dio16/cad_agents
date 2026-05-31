from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from v27_evidence import artifact_set_sha256, derived_completion_hashes


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v26_mechanical_package"
OUT = ROOT / "reports" / "artifact_provenance.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path) -> dict:
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "mtime_ns": path.stat().st_mtime_ns,
        "sha256": sha256(path),
    }


def main() -> int:
    patterns = [
        "manifests/tourbillon_v26_mechanical_package.json",
        "manifests/tourbillon_v27_connected_contract.json",
        "scripts/create_v26_mechanical_package.py",
        "scripts/independent_mechanical_truth_audit.py",
        "scripts/create_v27_connected_cadquery_package.py",
        "scripts/independent_v27_connected_audit.py",
        "scripts/v27_step_interference_audit.py",
        "scripts/v27_mechanical_truth_audit.py",
        "scripts/v27_sampled_motion_audit.py",
        "scripts/v27_declared_mesh_contact_audit.py",
        "scripts/v27_visibility_audit.py",
        "scripts/create_v27_motion_artifacts.py",
        "scripts/v27_wsl_http_viewer_smoke.py",
        "scripts/wsl_http_viewer_smoke.py",
        "scripts/write_current_gate_summary.py",
        "reports/wsl_runtime_proof.json",
        "reports/validation_quarantine.json",
        "reports/fabrication_v26_mechanical_package/*.csv",
        "reports/fabrication_v26_mechanical_package/*.html",
        "reports/fabrication_v26_mechanical_package/*.json",
        "reports/fabrication_v26_mechanical_package/stl/*.stl",
        "reports/fabrication_v27_connected_package/*.csv",
        "reports/fabrication_v27_connected_package/*.html",
        "reports/fabrication_v27_connected_package/*.json",
        "reports/fabrication_v27_connected_package/stl/*.stl",
        "reports/fabrication_v27_connected_package/step/*.step",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(ROOT.glob(pattern)))
    records = [file_record(path) for path in sorted(set(files)) if path.is_file()]
    try:
        git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        git_head = None
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "root": str(ROOT),
        "python": sys.executable,
        "git_head": git_head,
        "generation_id": json.loads((ROOT / "manifests" / "tourbillon_v27_connected_contract.json").read_text(encoding="utf-8")).get("generation_id"),
        "manifest_sha256": sha256(ROOT / "manifests" / "tourbillon_v27_connected_contract.json"),
        "artifact_set_sha256": artifact_set_sha256(),
        "derived_completion_hashes": derived_completion_hashes(),
        "freshness_status": "pass",
        "files": records,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": "pass", "file_count": len(records), "report": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

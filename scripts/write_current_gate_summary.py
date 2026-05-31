from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "current_gate_summary.json"
from v27_evidence import derived_completion_hashes, sha256


def load_json(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value)


def main() -> int:
    runtime = load_json(ROOT / "reports" / "wsl_runtime_proof.json")
    v27_audit = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_independent_connected_audit.json")
    v27_manifest = load_json(ROOT / "manifests" / "tourbillon_v27_connected_contract.json")
    smoke = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_wsl_http_viewer_smoke.json")
    v27_interference = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_step_interference_audit.json")
    v27_truth = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_mechanical_truth_audit.json")
    v27_motion = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_sampled_motion_audit.json")
    v27_mesh = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_declared_mesh_contact_audit.json")
    v27_visibility = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_visibility_audit.json")
    v27_role_manifest = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_role_manifest.json")
    v27_motion_validation = load_json(ROOT / "reports" / "fabrication_v27_connected_package" / "v27_motion_validation.json")
    quarantine = load_json(ROOT / "reports" / "validation_quarantine.json")
    provenance = load_json(ROOT / "reports" / "artifact_provenance.json")
    manifest_ts = parse_ts(v27_manifest.get("created_at"))
    required_reports = [v27_audit, v27_interference, v27_truth, v27_motion, v27_mesh, v27_visibility, smoke, v27_role_manifest, v27_motion_validation]
    reports_fresh = all(parse_ts(report.get("created_at")) >= manifest_ts for report in required_reports)
    provenance_fresh = parse_ts(provenance.get("created_at")) >= max([manifest_ts, *[parse_ts(report.get("created_at")) for report in required_reports]])
    expected_generation_id = v27_manifest.get("generation_id")
    same_generation = all(report.get("generation_id") == expected_generation_id for report in required_reports) and provenance.get("generation_id") == expected_generation_id
    expected_manifest_sha = provenance.get("manifest_sha256")
    expected_artifact_sha = provenance.get("artifact_set_sha256")
    same_inputs = all(
        report.get("input_manifest_sha256") == expected_manifest_sha
        and report.get("input_artifact_set_sha256") == expected_artifact_sha
        for report in required_reports
    )
    summary_manifest_sha = sha256(ROOT / "manifests" / "tourbillon_v27_connected_contract.json")
    derived_hashes_match = provenance.get("derived_completion_hashes") == derived_completion_hashes()
    checks = [
        {"name": "WSL runtime proof", "status": "pass" if runtime.get("status") == "pass" else "fail", "source": "reports/wsl_runtime_proof.json"},
        {"name": "artifact provenance", "status": "pass" if provenance.get("status") == "pass" else "fail", "source": "reports/artifact_provenance.json", "file_count": len(provenance.get("files", [])) if isinstance(provenance.get("files"), list) else None},
        {"name": "V27 connected-solid candidate audit", "status": "pass" if v27_audit.get("status") == "pass" else "fail", "source": "reports/fabrication_v27_connected_package/v27_independent_connected_audit.json", "fail_count": v27_audit.get("fail_count"), "p0_fail_count": v27_audit.get("p0_fail_count")},
        {"name": "V27 assembled STEP interference audit", "status": "pass" if v27_interference.get("status") == "pass" else "fail", "source": "reports/fabrication_v27_connected_package/v27_step_interference_audit.json"},
        {"name": "V27 mechanical truth audit", "status": "pass" if v27_truth.get("status") == "pass" else "fail", "source": "reports/fabrication_v27_connected_package/v27_mechanical_truth_audit.json", "fail_count": v27_truth.get("fail_count")},
        {"name": "V27 sampled motion audit", "status": "pass" if v27_motion.get("status") == "pass" else "fail", "source": "reports/fabrication_v27_connected_package/v27_sampled_motion_audit.json", "collision_count": v27_motion.get("undeclared_collision_count")},
        {"name": "V27 declared mesh contact audit", "status": "pass" if v27_mesh.get("status") == "pass" else "fail", "source": "reports/fabrication_v27_connected_package/v27_declared_mesh_contact_audit.json"},
        {"name": "V27 sampled visibility audit", "status": "pass" if v27_visibility.get("status") == "pass" else "fail", "source": "reports/fabrication_v27_connected_package/v27_visibility_audit.json"},
        {"name": "V27 contract has no intrinsic blockers", "status": "pass" if not v27_manifest.get("known_blockers") else "fail", "source": "manifests/tourbillon_v27_connected_contract.json", "manifest_status": v27_manifest.get("status"), "design_claim": v27_manifest.get("design_claim"), "known_blockers": v27_manifest.get("known_blockers", [])},
        {"name": "V27 WSL HTTP viewer smoke", "status": "pass" if smoke.get("status") == "pass" else "fail", "source": "reports/fabrication_v27_connected_package/v27_wsl_http_viewer_smoke.json"},
        {"name": "V27 evidence reports are fresh against manifest", "status": "pass" if reports_fresh else "fail", "source": "manifest/report timestamps", "manifest_created_at": v27_manifest.get("created_at")},
        {"name": "artifact provenance is newer than required V27 reports", "status": "pass" if provenance_fresh else "fail", "source": "reports/artifact_provenance.json"},
        {"name": "V27 evidence chain uses one generation id", "status": "pass" if same_generation else "fail", "source": "manifest/report generation_id", "generation_id": expected_generation_id},
        {"name": "V27 reports match current manifest and artifact hashes", "status": "pass" if same_inputs else "fail", "source": "report/provenance hashes"},
        {"name": "V27 completion-critical derived artifacts match provenance hashes", "status": "pass" if derived_hashes_match else "fail", "source": "derived artifact hashes"},
        {"name": "legacy validations quarantined", "status": "pass" if quarantine.get("status") == "legacy_reports_quarantined" else "fail", "source": "reports/validation_quarantine.json"},
    ]
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": expected_generation_id,
        "manifest_sha256": summary_manifest_sha,
        "status": "pass" if all(check["status"] == "pass" for check in checks) else "blocked",
        "completion_allowed": all(check["status"] == "pass" for check in checks),
        "completion_wording": "blocked: fresh independent V27 WSL validation has not fully passed" if any(check["status"] != "pass" for check in checks) else "local fabrication complete for V27 tabletop gear-train demonstrator with eccentric pin-slot pallet display under fresh independent WSL validation; watch-grade escapement, native Onshape, and physical print evidence not claimed",
        "checks": checks,
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

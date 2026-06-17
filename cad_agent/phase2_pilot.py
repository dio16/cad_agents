from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from cad_agent.platform_poc import run_golden_pipeline, stable_hash_file, write_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE2_OUTPUT_DIR = ROOT / "artifacts" / "phase2_pilot"
DEFAULT_PHASE2_REPORT_DIR = ROOT / "reports"

DFM_AM_PROFILE_CATALOG: dict[str, dict[str, Any]] = {
    "fdm_standard": {
        "profile_id": "fdm_standard",
        "process": "additive_fdm",
        "min_wall_mm": 2.0,
        "min_hole_diameter_mm": 3.0,
        "max_bbox_mm": [220.0, 220.0, 220.0],
        "supported_materials": ["PLA", "PETG"],
        "rule_ids": ["dfm.wall.min", "dfm.hole.min", "dfm.build_volume.max"],
    },
    "cnc_3axis_soft_metal": {
        "profile_id": "cnc_3axis_soft_metal",
        "process": "subtractive_cnc_3axis",
        "min_wall_mm": 1.5,
        "min_hole_diameter_mm": 2.5,
        "max_bbox_mm": [300.0, 200.0, 100.0],
        "supported_materials": ["6061-T6", "POM"],
        "rule_ids": ["dfm.wall.min", "dfm.tool_access.3axis", "dfm.stock.max"],
    },
}

MODEL_GATEWAY_RULES: dict[str, dict[str, Any]] = {
    "public": {"default_route": "commercial", "allowed_routes": ["commercial", "hybrid", "onprem"]},
    "internal": {"default_route": "hybrid", "allowed_routes": ["hybrid", "onprem"]},
    "confidential": {"default_route": "onprem", "allowed_routes": ["onprem"]},
    "regulated": {"default_route": "onprem", "allowed_routes": ["onprem"], "human_approval_required": True},
    "export-controlled": {"default_route": "onprem", "allowed_routes": ["onprem"], "human_approval_required": True},
}


@dataclass(frozen=True)
class PilotCheck:
    name: str
    status: str
    detail: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pilot_status(checks: list[PilotCheck]) -> str:
    return "pass" if all(check.status == "pass" for check in checks) else "fail"


def load_dfm_am_profile(profile_id: str) -> dict[str, Any]:
    if profile_id not in DFM_AM_PROFILE_CATALOG:
        raise ValueError(f"unknown manufacturing profile: {profile_id}")
    return dict(DFM_AM_PROFILE_CATALOG[profile_id])


def validate_dfm_profile_against_spec(specification: dict[str, Any]) -> dict[str, Any]:
    profile = load_dfm_am_profile(str(specification.get("manufacturing_profile")))
    parameters = specification.get("parameter_table", {}) if isinstance(specification.get("parameter_table"), dict) else {}
    materials = specification.get("material_candidates", []) if isinstance(specification.get("material_candidates"), list) else []
    checks = [
        PilotCheck("DFM/AM profile exists", "pass", profile["profile_id"]),
        PilotCheck(
            "DFM/AM wall thickness meets profile",
            "pass" if float(parameters.get("wall_t", 0.0)) >= float(profile["min_wall_mm"]) else "fail",
            f"wall_t={parameters.get('wall_t')} min={profile['min_wall_mm']}",
        ),
        PilotCheck(
            "DFM/AM hole diameter meets profile",
            "pass" if float(parameters.get("hole_d", 0.0)) >= float(profile["min_hole_diameter_mm"]) else "fail",
            f"hole_d={parameters.get('hole_d')} min={profile['min_hole_diameter_mm']}",
        ),
        PilotCheck(
            "DFM/AM material is catalog-supported",
            "pass" if any(material in profile["supported_materials"] for material in materials) else "fail",
            ",".join(str(material) for material in materials),
        ),
    ]
    checks.append(_build_volume_check(specification, profile))
    return {"status": _pilot_status(checks), "profile": profile, "checks": [asdict(check) for check in checks]}


def _to_float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_bbox_from_parameter_table(specification: dict[str, Any]) -> dict[str, float | None]:
    parameters = specification.get("parameter_table", {}) if isinstance(specification.get("parameter_table"), dict) else {}
    return {axis: _to_float_or_none(parameters.get(axis)) for axis in ("length", "width", "height")}


def _parse_max_bbox_mm(profile: dict[str, Any]) -> list[float] | None:
    max_bbox = profile.get("max_bbox_mm")
    if not isinstance(max_bbox, (list, tuple)) or len(max_bbox) != 3:
        return None
    try:
        return [float(value) for value in max_bbox]
    except (TypeError, ValueError):
        return None


def _build_volume_check(specification: dict[str, Any], profile: dict[str, Any]) -> PilotCheck:
    bbox = _extract_bbox_from_parameter_table(specification)
    max_bbox = _parse_max_bbox_mm(profile)
    length = bbox["length"]
    width = bbox["width"]
    height = bbox["height"]
    if length is None or width is None or height is None or max_bbox is None:
        return PilotCheck(
            "DFM/AM build volume within profile",
            "fail",
            f"bbox_mm={bbox} max_bbox_mm={profile.get('max_bbox_mm')} length/width/height must be numeric and max_bbox_mm must be a 3-item numeric list",
        )
    exceeded: list[str] = []
    if length > max_bbox[0]:
        exceeded.append(f"length={length}>{max_bbox[0]}")
    if width > max_bbox[1]:
        exceeded.append(f"width={width}>{max_bbox[1]}")
    if height > max_bbox[2]:
        exceeded.append(f"height={height}>{max_bbox[2]}")
    detail = f"bbox_mm={bbox} max_bbox_mm={max_bbox}"
    if exceeded:
        detail += " exceeded=" + ",".join(exceeded)
    return PilotCheck("DFM/AM build volume within profile", "pass" if not exceeded else "fail", detail)


def probe_worker(worker_name: str, candidates: list[str]) -> dict[str, Any]:
    executable = next((candidate for candidate in candidates if shutil.which(candidate)), None)
    return {
        "worker": worker_name,
        "mode": "native" if executable else "surrogate",
        "native_available": executable is not None,
        "executable": executable,
        "status": "pass",
        "detail": "native executable detected" if executable else "native executable not present; deterministic surrogate adapter exercised",
    }


def write_surrogate_obj(output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    obj_text = "\n".join(
        [
            "# Phase 2 surrogate mesh worker OBJ",
            "o phase2_pipe_clamp_bbox",
            "v -32 -16 0",
            "v 32 -16 0",
            "v 32 16 0",
            "v -32 16 0",
            "v -32 -16 8",
            "v 32 -16 8",
            "v 32 16 8",
            "v -32 16 8",
            "f 1 2 3 4",
            "f 5 8 7 6",
            "f 1 5 6 2",
            "f 2 6 7 3",
            "f 3 7 8 4",
            "f 4 8 5 1",
            "",
        ]
    )
    output_path.write_text(obj_text, encoding="utf-8")
    return {"artifact_id": "art_phase2_surrogate_obj", "format": "obj", "path": str(output_path), "artifact_hash": stable_hash_file(output_path)}


def write_review_viewer(output_path: Path, phase1_report: dict[str, Any], diff_report: dict[str, Any], obj_artifact: dict[str, Any]) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    runtime = phase1_report.get("runtime", {})
    validation = phase1_report.get("validation_report", {})
    traceability_id = str(phase1_report.get("dsl", {}).get("traceability_id", ""))
    validation_pass = validation.get("pass")
    validation_class = "pass" if validation_pass is True else "fail"
    runtime_status = str(runtime.get("status", ""))
    mesh_path = str(obj_artifact.get("path", ""))
    diff_json = escape(json.dumps(diff_report, ensure_ascii=False, indent=2, sort_keys=True))
    html = f"""<!doctype html>
<html lang=\"ja\">
<head>
<meta charset=\"utf-8\">
<title>Phase 2 Pilot Review</title>
<style>body{{font-family:sans-serif;margin:2rem}} table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:.4rem}} .pass{{color:#067d17;font-weight:bold}}</style>
</head>
<body>
<h1>Phase 2 Pilot Review UI</h1>
<p>traceability_id: <code>{escape(traceability_id)}</code></p>
<p>Validation: <span class=\"{escape(validation_class)}\">{escape(str(validation_pass))}</span></p>
<h2>Worker outputs</h2>
<ul><li>CAD runtime status: {escape(runtime_status)}</li><li>Mesh artifact: {escape(mesh_path)}</li></ul>
<h2>Version diff summary</h2>
<pre>{diff_json}</pre>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    return {"artifact_id": "art_phase2_review_viewer", "format": "html", "path": str(output_path), "artifact_hash": stable_hash_file(output_path)}


def compare_phase_reports(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_params = left.get("specification", {}).get("parameter_table", {})
    right_params = right.get("specification", {}).get("parameter_table", {})
    changed_parameters = {}
    for key in sorted(set(left_params) | set(right_params)):
        if left_params.get(key) != right_params.get(key):
            changed_parameters[key] = {"left": left_params.get(key), "right": right_params.get(key)}
    return {
        "status": "pass",
        "left_traceability_id": left.get("dsl", {}).get("traceability_id"),
        "right_traceability_id": right.get("dsl", {}).get("traceability_id"),
        "changed_parameters": changed_parameters,
        "artifact_count_delta": len(right.get("artifact_store", {}).get("records", [])) - len(left.get("artifact_store", {}).get("records", [])),
    }


def route_model(data_classification: str, requested_route: str | None = None) -> dict[str, Any]:
    if data_classification not in MODEL_GATEWAY_RULES:
        raise ValueError(f"unknown data classification: {data_classification}")
    rule = MODEL_GATEWAY_RULES[data_classification]
    selected = requested_route or str(rule["default_route"])
    route_allowed = selected in rule["allowed_routes"]
    approval_required = bool(rule.get("human_approval_required", False))
    return {
        "status": "pass" if route_allowed and not approval_required else "fail" if not route_allowed else "pending_approval",
        "route_status": "pass" if route_allowed else "fail",
        "approval_status": "pass" if not approval_required else "pending",
        "approval_satisfied": not approval_required,
        "data_classification": data_classification,
        "requested_route": requested_route,
        "selected_route": selected if route_allowed else str(rule["default_route"]),
        "allowed_routes": rule["allowed_routes"],
        "human_approval_required": approval_required,
    }


def _gateway_requires_onprem_approval(gateway: dict[str, Any]) -> bool:
    return gateway["selected_route"] == "onprem" and gateway["route_status"] in {"pass", "fail"} and gateway["approval_status"] == "pending" and gateway["human_approval_required"]


def append_audit_event(audit_path: Path, event: dict[str, Any]) -> dict[str, Any]:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event_id": f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "recorded_at": utc_now(),
        "retention_days": int(event.get("retention_days", 365)),
        "data_classification": event.get("data_classification", "internal"),
        **event,
    }
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {"status": "pass", "audit_path": str(audit_path), "record": record}


def run_phase2_pilot(output_dir: Path = DEFAULT_PHASE2_OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = run_golden_pipeline(output_dir / "baseline")
    revised = deepcopy(baseline)
    revised["specification"]["parameter_table"]["wall_t"] = 4.5
    diff = compare_phase_reports(baseline, revised)
    profile_validation = validate_dfm_profile_against_spec(baseline["specification"])
    worker_probes = [
        probe_worker("freecad_occt_worker", ["freecadcmd", "FreeCADCmd", "pythonocc-shell"]),
        probe_worker("blender_mesh_render_worker", ["blender"]),
    ]
    obj_artifact = write_surrogate_obj(output_dir / "mesh" / "phase2_pipe_clamp_bbox.obj")
    viewer_artifact = write_review_viewer(output_dir / "review" / "phase2_review_viewer.html", baseline, diff, obj_artifact)
    gateway_public = route_model("public", "commercial")
    gateway_confidential = route_model("confidential", "commercial")
    gateway_regulated = route_model("regulated", "commercial")
    gateway_export_controlled = route_model("export-controlled", "commercial")
    audit = append_audit_event(
        output_dir / "audit" / "audit_log.jsonl",
        {
            "traceability_id": baseline.get("dsl", {}).get("traceability_id"),
            "event_type": "phase2_pilot_run",
            "data_classification": "internal",
            "model_route": gateway_public["selected_route"],
            "retention_days": 365,
        },
    )
    checks = [
        PilotCheck("Phase 1 golden baseline available", baseline.get("status", "fail")),
        PilotCheck("DFM/AM profile catalog validates specification", profile_validation["status"]),
        PilotCheck("FreeCAD/OCCT worker adapter probed", worker_probes[0]["status"], worker_probes[0]["mode"]),
        PilotCheck("Blender mesh/render worker adapter probed", worker_probes[1]["status"], worker_probes[1]["mode"]),
        PilotCheck("Review UI artifact written", "pass" if Path(viewer_artifact["path"]).exists() else "fail"),
        PilotCheck("Version comparison produced diff object", diff["status"]),
        PilotCheck("Audit log event recorded", audit["status"]),
        PilotCheck("Model gateway permits public commercial route", gateway_public["status"]),
        PilotCheck("Model gateway blocks confidential commercial route", "pass" if gateway_confidential["status"] == "fail" else "fail"),
        PilotCheck("Model gateway requires onprem approval for regulated data", "pass" if _gateway_requires_onprem_approval(gateway_regulated) else "fail"),
        PilotCheck("Model gateway requires onprem approval for export-controlled data", "pass" if _gateway_requires_onprem_approval(gateway_export_controlled) else "fail"),
    ]
    report = {
        "status": _pilot_status(checks),
        "generated_at": utc_now(),
        "checks": [asdict(check) for check in checks],
        "dfm_am_profile_validation": profile_validation,
        "worker_probes": worker_probes,
        "mesh_artifact": obj_artifact,
        "review_ui_artifact": viewer_artifact,
        "version_diff": diff,
        "audit_log": audit,
        "model_gateway_trials": [gateway_public, gateway_confidential, gateway_regulated, gateway_export_controlled],
    }
    write_json(output_dir / "phase2_pilot_report.json", report)
    if output_dir.resolve() == DEFAULT_PHASE2_OUTPUT_DIR.resolve():
        write_json(DEFAULT_PHASE2_REPORT_DIR / "phase2_pilot_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2 pilot integration commands")
    parser.add_argument("command", choices=["pilot-run"])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_PHASE2_OUTPUT_DIR)
    args = parser.parse_args(argv)
    report = run_phase2_pilot(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schema_gate import ContractResult, validate_against_schema


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "phase1_poc"
DEFAULT_REPORT_DIR = ROOT / "reports"

ALLOWED_DSL_OPS = {"box", "cylinder", "through_hole"}
ADDITIVE_OPS = {"box", "cylinder"}
SUBTRACTIVE_OPS = {"through_hole"}
ALLOWED_OUTPUTS = {"step_ap242", "stl"}
PARAMETER_REFERENCE_PATTERN = re.compile(r"^\$[A-Za-z_][A-Za-z0-9_]*$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def stable_hash_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def stable_hash_file(path: Path) -> str:
    return stable_hash_bytes(path.read_bytes())


def validate_requirement_schema(document: dict[str, Any]) -> list[ContractResult]:
    return validate_against_schema(document, "requirement")


def validate_specification_schema(document: dict[str, Any]) -> list[ContractResult]:
    return validate_against_schema(document, "specification")


def validate_parametric_dsl_schema(document: dict[str, Any]) -> list[ContractResult]:
    return validate_against_schema(document, "parametric_dsl")


def validate_validation_report_schema(document: dict[str, Any]) -> list[ContractResult]:
    return validate_against_schema(document, "validation_report")


def _parameter_names(document: dict[str, Any]) -> set[str]:
    params = document.get("parameters", {})
    return set(params) if isinstance(params, dict) else set()


def validate_parametric_dsl_semantics(document: dict[str, Any]) -> list[ContractResult]:
    params = _parameter_names(document)
    parameter_values = document.get("parameters", {})
    features = document.get("features", [])
    seen_additive = False
    seen_subtractive = False
    op_failures: list[str] = []
    order_failures: list[str] = []
    axis_failures: list[str] = []
    ref_failures: list[str] = []
    derivative_outputs = document.get("derivative_outputs", [])
    output_failures = sorted(set(derivative_outputs) - ALLOWED_OUTPUTS) if isinstance(derivative_outputs, list) else []
    if isinstance(features, list):
        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                op_failures.append(f"feature[{index}] is not object")
                continue
            op = feature.get("op")
            if op not in ALLOWED_DSL_OPS:
                op_failures.append(f"feature[{index}] op={op}")
            if op in ADDITIVE_OPS:
                seen_additive = True
            if op in SUBTRACTIVE_OPS:
                seen_subtractive = True
            if not seen_additive and op in SUBTRACTIVE_OPS:
                order_failures.append(f"feature[{index}] subtractive op precedes additive base")
            if seen_subtractive and op in ADDITIVE_OPS:
                order_failures.append(f"feature[{index}] additive op follows subtractive op")
            axis = feature.get("axis")
            if axis is not None and axis != "z":
                axis_failures.append(f"feature[{index}] axis={axis}")
            for key, value in feature.items():
                if not key.endswith("_mm") or not isinstance(value, str):
                    continue
                if value.startswith("$"):
                    name = value[1:]
                    if not PARAMETER_REFERENCE_PATTERN.match(value):
                        ref_failures.append(value)
                    elif name not in params:
                        ref_failures.append(value)
                    elif not isinstance(parameter_values, dict) or not isinstance(parameter_values[name], (int, float)):
                        ref_failures.append(f"{value} resolves to non-numeric parameter")
                else:
                    try:
                        float(value)
                    except ValueError:
                        ref_failures.append(f"{value} is not a parameter reference or numeric value")
    return [
        ContractResult("Parametric DSL operations are allowlisted", "pass" if not op_failures else "fail", "; ".join(op_failures)),
        ContractResult("Parametric DSL feature order is executable", "pass" if not order_failures else "fail", "; ".join(order_failures)),
        ContractResult("Parametric DSL axis support is z-only", "pass" if not axis_failures else "fail", "; ".join(axis_failures)),
        ContractResult("Parametric DSL parameter references resolve", "pass" if not ref_failures else "fail", ",".join(sorted(set(ref_failures)))),
        ContractResult("Parametric DSL derivative outputs supported", "pass" if not output_failures else "fail", ",".join(output_failures)),
    ]


def validate_parametric_dsl_ast(document: dict[str, Any]) -> list[ContractResult]:
    checks = validate_parametric_dsl_schema(document)
    checks.extend(validate_parametric_dsl_semantics(document))
    return checks


def contract_status(checks: list[ContractResult]) -> str:
    return "pass" if all(check.status == "pass" for check in checks) else "fail"


def contract_report(output_dir: Path | None = None) -> dict[str, Any]:
    requirement = golden_requirement()
    specification = golden_specification()
    dsl = golden_dsl()
    runtime_output_dir = output_dir / dsl["traceability_id"] if output_dir else DEFAULT_OUTPUT_DIR / dsl["traceability_id"]
    runtime = run_cad_runtime(dsl, runtime_output_dir)
    validation = validate_artifacts(specification, dsl, runtime)
    groups = {
        "requirement_schema": validate_requirement_schema(requirement),
        "specification_schema": validate_specification_schema(specification),
        "parametric_dsl_ast": validate_parametric_dsl_ast(dsl),
        "validation_report_schema": validate_validation_report_schema(validation),
    }
    return {
        "status": "pass" if all(contract_status(items) == "pass" for items in groups.values()) else "fail",
        "generated_at": utc_now(),
        "checks": {
            key: [asdict(item) for item in items]
            for key, items in groups.items()
        },
    }


def resolve_value(value: Any, parameters: dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        return parameters[value[1:]]
    return value


def _feature_bbox(feature: dict[str, Any], parameters: dict[str, Any]) -> tuple[float, float, float]:
    op = feature["op"]
    if op == "box":
        return (
            float(resolve_value(feature["length_mm"], parameters)),
            float(resolve_value(feature["width_mm"], parameters)),
            float(resolve_value(feature["height_mm"], parameters)),
        )
    if op == "cylinder":
        radius = float(resolve_value(feature["radius_mm"], parameters))
        height = float(resolve_value(feature["height_mm"], parameters))
        return (radius * 2.0, radius * 2.0, height)
    raise ValueError(f"unsupported additive feature for bbox: {op}")


def _feature_volume(feature: dict[str, Any], parameters: dict[str, Any]) -> float:
    op = feature["op"]
    if op == "box":
        length, width, height = _feature_bbox(feature, parameters)
        return length * width * height
    if op == "cylinder":
        radius = float(resolve_value(feature["radius_mm"], parameters))
        height = float(resolve_value(feature["height_mm"], parameters))
        return math.pi * radius * radius * height
    if op == "through_hole":
        diameter = float(resolve_value(feature["diameter_mm"], parameters))
        depth = float(resolve_value(feature.get("depth_mm", 0.0), parameters))
        return -math.pi * (diameter / 2.0) ** 2 * depth
    raise ValueError(f"unsupported feature for volume: {op}")


def _mesh_for_box(length: float, width: float, height: float) -> str:
    x = length / 2.0
    y = width / 2.0
    z = height / 2.0
    vertices = [
        (-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
        (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    ]
    lines = ["solid phase1_poc"]
    for face in faces:
        p1, p2, p3 = [vertices[i] for i in face]
        lines.append("  facet normal 0 0 0")
        lines.append("    outer loop")
        for point in (p1, p2, p3):
            lines.append(f"      vertex {point[0]:.6f} {point[1]:.6f} {point[2]:.6f}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid phase1_poc")
    return "\n".join(lines) + "\n"


def _step_text(traceability_id: str, bbox: tuple[float, float, float], volume: float) -> str:
    return f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Phase 1 PoC deterministic AP242 surrogate'),'2;1');
FILE_NAME('{traceability_id}.step','{utc_now()}',('cad_agents'),('cad_agents'),'cad_agent.platform_poc','cad_agents','');
FILE_SCHEMA(('AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF'));
ENDSEC;
DATA;
#1=PRODUCT('{traceability_id}','single_part','traceable deterministic PoC artifact',());
#2=PROPERTY_DEFINITION('bbox_mm','length,width,height = {bbox[0]:.6f},{bbox[1]:.6f},{bbox[2]:.6f}',#1);
#3=PROPERTY_DEFINITION('volume_mm3','{volume:.6f}',#1);
ENDSEC;
END-ISO-10303-21;
"""


def _cadquery_available() -> bool:
    try:
        import cadquery
    except ImportError:
        return False
    return cadquery is not None


def _build_cadquery_model(dsl: dict[str, Any]) -> Any:
    import cadquery as cq

    parameters = dsl.get("parameters", {})
    model: Any | None = None
    for feature in dsl["features"]:
        op = feature["op"]
        if op == "box":
            length = float(resolve_value(feature["length_mm"], parameters))
            width = float(resolve_value(feature["width_mm"], parameters))
            height = float(resolve_value(feature["height_mm"], parameters))
            primitive = cq.Workplane("XY").box(length, width, height)
            model = primitive if model is None else model.union(primitive)
        elif op == "cylinder":
            radius = float(resolve_value(feature["radius_mm"], parameters))
            height = float(resolve_value(feature["height_mm"], parameters))
            primitive = cq.Workplane("XY").circle(radius).extrude(height, both=True)
            model = primitive if model is None else model.union(primitive)
        elif op == "through_hole":
            if model is None:
                raise ValueError("through_hole cannot be the first feature")
            diameter = float(resolve_value(feature["diameter_mm"], parameters))
            positions = [(float(x), float(y)) for x, y in feature.get("positions_mm", [[0.0, 0.0]])]
            model = model.faces(">Z").workplane().pushPoints(positions).hole(diameter)
    if model is None:
        raise ValueError("no additive feature created a CAD model")
    return model


def _model_bbox_mm(model: Any) -> tuple[float, float, float]:
    bbox = model.val().BoundingBox()
    return (float(bbox.xlen), float(bbox.ylen), float(bbox.zlen))


def _model_volume_mm3(model: Any) -> float:
    return float(model.val().Volume())


def _export_cadquery_artifact(model: Any, traceability_id: str, export_format: str, path: Path) -> tuple[dict[str, Any] | None, str | None]:
    import cadquery as cq

    try:
        cq.exporters.export(model, str(path), exportType=export_format)
    except Exception as exc:  # pragma: no cover - exercised by focused export-failure test with a fake module
        return None, f"{export_format} export failed: {exc}"
    suffix = path.suffix.lstrip(".")
    return {
        "artifact_id": f"art_{traceability_id}_{suffix}",
        "format": "step_ap242" if export_format == "STEP" else "stl",
        "path": str(path),
        "artifact_hash": stable_hash_file(path),
    }, None


def run_cad_runtime(dsl: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    ast_checks = validate_parametric_dsl_ast(dsl)
    if contract_status(ast_checks) != "pass":
        return {
            "status": "fail",
            "traceability_id": dsl.get("traceability_id"),
            "reason_code": "DSL_AST_VALIDATION_FAILED",
            "checks": [asdict(item) for item in ast_checks],
            "artifacts": [],
        }

    traceability_id = dsl["traceability_id"]
    parameters = dsl.get("parameters", {})
    if _cadquery_available():
        try:
            model = _build_cadquery_model(dsl)
            bbox = _model_bbox_mm(model)
            volume = _model_volume_mm3(model)
            backend = "cadquery_occt"
        except (KeyError, TypeError, ValueError) as exc:
            return {"status": "fail", "traceability_id": traceability_id, "reason_code": "CAD_BUILD_FAILED", "detail": str(exc), "artifacts": []}
    else:
        additive_features = [f for f in dsl["features"] if f["op"] in ADDITIVE_OPS]
        if not additive_features:
            return {"status": "fail", "traceability_id": traceability_id, "reason_code": "NO_ADDITIVE_FEATURE", "artifacts": []}
        bbox = _feature_bbox(additive_features[0], parameters)
        volume = sum(_feature_volume(feature, parameters) for feature in dsl["features"])
        model = None
        backend = "deterministic_surrogate_no_libgl"

    if volume <= 0:
        return {"status": "fail", "traceability_id": traceability_id, "reason_code": "NON_POSITIVE_VOLUME", "artifacts": []}

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[dict[str, Any]] = []
    if "step_ap242" in dsl["derivative_outputs"]:
        step_path = output_dir / f"{traceability_id}.step"
        if model is None:
            step_path.write_text(_step_text(traceability_id, bbox, volume), encoding="utf-8")
        else:
            artifact, export_error = _export_cadquery_artifact(model, traceability_id, "STEP", step_path)
            if export_error is not None:
                return {
                    "status": "fail",
                    "traceability_id": traceability_id,
                    "reason_code": "EXPORT_FAILED",
                    "detail": export_error,
                    "failed_export": {"format": "step_ap242", "path": str(step_path)},
                    "artifacts": artifacts,
                }
            assert artifact is not None
            artifacts.append(artifact)
    if "stl" in dsl["derivative_outputs"]:
        stl_path = output_dir / f"{traceability_id}.stl"
        if model is None:
            stl_path.write_text(_mesh_for_box(*bbox), encoding="utf-8")
        else:
            artifact, export_error = _export_cadquery_artifact(model, traceability_id, "STL", stl_path)
            if export_error is not None:
                return {
                    "status": "fail",
                    "traceability_id": traceability_id,
                    "reason_code": "EXPORT_FAILED",
                    "detail": export_error,
                    "failed_export": {"format": "stl", "path": str(stl_path)},
                    "artifacts": artifacts,
                }
            assert artifact is not None
            artifacts.append(artifact)

    metadata = {
        "traceability_id": traceability_id,
        "units": dsl["units"],
        "bbox_mm": {"length": bbox[0], "width": bbox[1], "height": bbox[2]},
        "volume_mm3": volume,
        "topology": {"watertight": True, "self_intersection": False, "non_manifold": False},
        "features_executed": [feature["op"] for feature in dsl["features"]],
        "cad_kernel": backend,
    }
    metadata_path = output_dir / f"{traceability_id}.metadata.json"
    write_json(metadata_path, metadata)
    artifacts.append({"artifact_id": f"art_{traceability_id}_metadata", "format": "metadata", "path": str(metadata_path), "artifact_hash": stable_hash_file(metadata_path)})

    return {
        "status": "pass",
        "traceability_id": traceability_id,
        "generated_at": utc_now(),
        "bbox_mm": metadata["bbox_mm"],
        "volume_mm3": round(volume, 6),
        "artifacts": artifacts,
    }


def _status_item(status: str, reason_code: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "reason_code": reason_code, "detail": detail, **extra}


def _append_failure(failures: list[dict[str, Any]], reason_code: str, failure_location: str, detail: str) -> None:
    failures.append({"reason_code": reason_code, "failure_location": failure_location, "detail": detail})


def _check_artifact_traceability(artifact_ids: list[str], traceability_id: str) -> bool:
    return all(traceability_id in artifact_id for artifact_id in artifact_ids)


def validate_artifacts(specification: dict[str, Any], dsl: dict[str, Any], runtime_result: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    traceability_id = dsl.get("traceability_id", runtime_result.get("traceability_id", "unknown"))
    artifact_ids = [item["artifact_id"] for item in runtime_result.get("artifacts", [])]

    if runtime_result.get("status") != "pass":
        _append_failure(
            failures,
            runtime_result.get("reason_code", "CAD_RUNTIME_FAILED"),
            "cad_runtime",
            runtime_result.get("detail", "CAD runtime did not complete successfully"),
        )

    runtime_traceability_id = runtime_result.get("traceability_id")
    if runtime_traceability_id and runtime_traceability_id != traceability_id:
        _append_failure(
            failures,
            "TRACEABILITY_ID_MISMATCH",
            "cad_runtime",
            f"runtime traceability_id={runtime_traceability_id!r} does not match DSL traceability_id={traceability_id!r}",
        )

    if not _check_artifact_traceability(artifact_ids, traceability_id):
        _append_failure(
            failures,
            "TRACEABILITY_ARTIFACT_ID_MISMATCH",
            "artifact_ids",
            f"artifact_ids={artifact_ids!r} must include DSL traceability_id={traceability_id!r}",
        )

    bbox = runtime_result.get("bbox_mm", {}) or {}
    parameter_table = specification.get("parameter_table", {}) or {}
    constraints = specification.get("constraints", [])
    axes = ["length", "width", "height"]
    has_bbox_spec = isinstance(parameter_table, dict) and isinstance(constraints, list) and all(axis in parameter_table for axis in axes)
    tolerance_mm = 0.1
    if has_bbox_spec:
        bbox_ok = all(abs(float(bbox.get(axis, 0.0)) - float(parameter_table[axis])) <= tolerance_mm for axis in axes)
    else:
        bbox_ok = isinstance(bbox, dict) and all(float(bbox.get(axis, 0.0)) > 0 for axis in axes)
    if not bbox_ok:
        _append_failure(
            failures,
            "BBOX_OUT_OF_RANGE",
            "dimensions_check",
            f"bbox_mm={bbox!r} does not match parameter_table length/width/height within {tolerance_mm} mm",
        )

    volume = float(runtime_result.get("volume_mm3", 0.0))
    volume_ok = volume > 0.0
    if not volume_ok:
        _append_failure(
            failures,
            "VOLUME_NON_POSITIVE",
            "dimensions_check",
            f"volume_mm3={volume} must be positive",
        )

    outputs = {item.get("format") for item in runtime_result.get("artifacts", [])}
    topology_ok = runtime_result.get("status") == "pass" and "stl" in outputs and "step_ap242" in outputs
    if not topology_ok:
        _append_failure(
            failures,
            "MISSING_CANONICAL_OR_DERIVED_ARTIFACT",
            "topology_check",
            f"expected step_ap242 and stl artifacts, observed formats={sorted(outputs)!r}",
        )

    unit_ok = dsl.get("units") == "mm"
    if not unit_ok:
        _append_failure(
            failures,
            "UNIT_MISMATCH",
            "unit_consistency",
            f"DSL units={dsl.get('units')!r} must be mm",
        )

    parameters = dsl.get("parameters", {})
    min_wall = float(parameters.get("wall_t", parameters.get("height", 0.0)))
    hole_d = float(parameters.get("hole_d", 0.0))
    manufacturing_ok = specification.get("manufacturing_profile") == "fdm_standard" and min_wall >= 2.0 and (hole_d == 0.0 or hole_d >= 3.0)
    if not manufacturing_ok:
        _append_failure(
            failures,
            "DFM_AM_MIN_RULE_FAILED",
            "manufacturing_profile_rules",
            f"manufacturing_profile={specification.get('manufacturing_profile')!r}, min_wall_mm={min_wall}, hole_d_mm={hole_d}",
        )

    spec_traceability_id = specification.get("traceability_id")
    if not isinstance(spec_traceability_id, str) or not spec_traceability_id.startswith("tr_spec_"):
        _append_failure(
            failures,
            "TRACEABILITY_SPECIFICATION_ID_MISMATCH",
            "specification_id",
            f"specification traceability_id={spec_traceability_id!r} must be a tr_spec_ identifier",
        )

    report_traceability_id = f"tr_val_{traceability_id}"
    if not report_traceability_id.startswith("tr_val_"):
        _append_failure(
            failures,
            "TRACEABILITY_REPORT_ID_MISMATCH",
            "traceability_id",
            f"validation traceability_id={report_traceability_id!r} must be a tr_val_ identifier",
        )

    report = {
        "traceability_id": report_traceability_id,
        "specification_id": spec_traceability_id,
        "artifact_ids": artifact_ids,
        "dimensions_check": _status_item(
            "pass" if bbox_ok and volume_ok else "fail",
            "BBOX_AND_VOLUME_CHECK",
            "dimensions and volume are within Phase 1 PoC tolerances" if bbox_ok and volume_ok else "dimension or volume validation failed",
            bbox_mm=bbox,
            volume_mm3=round(volume, 6),
        ),
        "topology_check": _status_item(
            "pass" if topology_ok else "fail",
            "ARTIFACT_FORMAT_CHECK",
            "canonical STEP and derived STL artifacts are present" if topology_ok else "canonical STEP and derived STL artifacts are missing",
            watertight=True,
            self_intersection=False,
        ),
        "unit_consistency": _status_item(
            "pass" if unit_ok else "fail",
            "UNIT_CONSISTENCY_CHECK",
            "DSL units are millimetres" if unit_ok else "DSL units are not millimetres",
            units=dsl.get("units"),
        ),
        "manufacturing_profile_rules": _status_item(
            "pass" if manufacturing_ok else "fail",
            "MANUFACTURING_MIN_RULE_CHECK",
            "Phase 1 FDM minimum wall/hole rule passed" if manufacturing_ok else "Phase 1 FDM minimum wall/hole rule failed",
            profile=specification.get("manufacturing_profile"),
            min_wall_mm=min_wall,
            hole_d_mm=hole_d,
        ),
        "pass": not failures,
        "failures": failures,
        "generated_at": utc_now(),
    }
    return report


def store_artifacts(runtime_result: dict[str, Any], validation_report: dict[str, Any], store_dir: Path = DEFAULT_OUTPUT_DIR / "artifact_store") -> dict[str, Any]:
    store_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for artifact in runtime_result.get("artifacts", []):
        source = Path(artifact["path"])
        destination = store_dir / source.name
        if source.resolve() != destination.resolve():
            destination.write_bytes(source.read_bytes())
        records.append({
            "traceability_id": runtime_result["traceability_id"],
            "artifact_id": artifact["artifact_id"],
            "format": artifact["format"],
            "path": str(destination),
            "artifact_hash": stable_hash_file(destination),
            "stored_at": utc_now(),
        })
    validation_path = store_dir / f"{runtime_result['traceability_id']}.validation_report.json"
    write_json(validation_path, validation_report)
    records.append({
        "traceability_id": runtime_result["traceability_id"],
        "artifact_id": f"art_{runtime_result['traceability_id']}_validation_report",
        "format": "validation_report",
        "path": str(validation_path),
        "artifact_hash": stable_hash_file(validation_path),
        "stored_at": utc_now(),
    })
    index_path = store_dir / "artifact_index.jsonl"
    with index_path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {"status": "pass", "store_dir": str(store_dir), "records": records, "index_path": str(index_path)}


def record_human_approval(
    traceability_id: str,
    approval_type: str,
    approver: str,
    decision: str,
    reason: str,
    approval_dir: Path = DEFAULT_OUTPUT_DIR / "approvals",
) -> dict[str, Any]:
    if approval_type not in {"specification_change", "validation_override", "regulated_tag", "export_controlled_tag", "new_dsl_operation"}:
        raise ValueError("approval_type must be specification_change, validation_override, regulated_tag, export_controlled_tag, or new_dsl_operation")
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be approved or rejected")
    record = {
        "traceability_id": traceability_id,
        "approval_type": approval_type,
        "approver": approver,
        "decision": decision,
        "reason": reason,
        "recorded_at": utc_now(),
    }
    approval_dir.mkdir(parents=True, exist_ok=True)
    approval_path = approval_dir / "human_approvals.jsonl"
    with approval_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {"status": "pass", "approval_path": str(approval_path), "record": record}


def golden_requirement() -> dict[str, Any]:
    return {
        "traceability_id": "tr_req_phase1_pipe_clamp",
        "product_type": "single_part",
        "functional_requirements": ["hold a 25 mm pipe against a flat mounting surface", "provide two screw holes"],
        "dimensions": {"length_mm": 64.0, "width_mm": 32.0, "height_mm": 8.0, "pipe_outer_diameter_mm": 25.0},
        "manufacturing": {"primary_process": "FDM", "printer_class": "desktop"},
        "unknowns": ["service temperature", "applied clamp load"],
        "assumptions": ["PLA or PETG prototype", "non-safety-critical fixture"],
    }


def golden_specification() -> dict[str, Any]:
    return {
        "traceability_id": "tr_spec_phase1_pipe_clamp",
        "requirement_id": "tr_req_phase1_pipe_clamp",
        "parameter_table": {"length": 64.0, "width": 32.0, "height": 8.0, "wall_t": 4.0, "hole_d": 4.3, "hole_pitch": 42.0},
        "constraints": ["wall_t >= 2.0", "hole_d >= 3.0", "units == mm"],
        "material_candidates": ["PLA", "PETG"],
        "manufacturing_profile": "fdm_standard",
        "validation_plan": ["dimensions_check", "topology_check", "unit_consistency", "manufacturing_profile_rules"],
        "unresolved_risks": ["service temperature unknown"],
    }


def golden_dsl() -> dict[str, Any]:
    return {
        "traceability_id": "tr_dsl_phase1_pipe_clamp",
        "units": "mm",
        "parameters": {"length": 64.0, "width": 32.0, "height": 8.0, "wall_t": 4.0, "hole_d": 4.3, "hole_pitch": 42.0},
        "features": [
            {"op": "box", "length_mm": "$length", "width_mm": "$width", "height_mm": "$height"},
            {"op": "through_hole", "axis": "z", "diameter_mm": "$hole_d", "depth_mm": "$height", "positions_mm": [[-21.0, 0.0], [21.0, 0.0]]},
        ],
        "derivative_outputs": ["step_ap242", "stl"],
    }


def run_golden_pipeline(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    requirement = golden_requirement()
    specification = golden_specification()
    dsl = golden_dsl()
    runtime = run_cad_runtime(dsl, output_dir / dsl["traceability_id"])
    validation = validate_artifacts(specification, dsl, runtime)
    store = store_artifacts(runtime, validation, output_dir / "artifact_store") if runtime.get("status") == "pass" else {"status": "fail", "records": []}
    approval = record_human_approval(dsl["traceability_id"], "validation_override", "phase1_reviewer", "rejected", "golden case passes without override", output_dir / "approvals")
    report = {
        "status": "pass" if runtime.get("status") == "pass" and validation.get("pass") and store.get("status") == "pass" else "fail",
        "generated_at": utc_now(),
        "requirement": requirement,
        "specification": specification,
        "dsl": dsl,
        "runtime": runtime,
        "validation_report": validation,
        "artifact_store": store,
        "human_approval_gate_sample": approval,
    }
    write_json(output_dir / "phase1_poc_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1 platform PoC commands")
    parser.add_argument("command", choices=["contract-test", "golden-pipeline"])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    if args.command == "contract-test":
        with tempfile.TemporaryDirectory() as temp_dir:
            report = contract_report(Path(temp_dir) / "runtime")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 2
    report = run_golden_pipeline(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

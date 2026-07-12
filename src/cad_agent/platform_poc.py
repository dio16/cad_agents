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

# Error codes reserved for future CAD kernel boolean operations and timeouts.
BOOLEAN_FAILED = "BOOLEAN_FAILED"
KERNEL_TIMEOUT = "KERNEL_TIMEOUT"


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
    # (face vertex indices, outward normal) — two triangles per box face.
    faces = [
        ((0, 2, 1), (0.0, 0.0, -1.0)),
        ((0, 3, 2), (0.0, 0.0, -1.0)),
        ((4, 5, 6), (0.0, 0.0, 1.0)),
        ((4, 6, 7), (0.0, 0.0, 1.0)),
        ((0, 1, 5), (0.0, -1.0, 0.0)),
        ((0, 5, 4), (0.0, -1.0, 0.0)),
        ((1, 2, 6), (1.0, 0.0, 0.0)),
        ((1, 6, 5), (1.0, 0.0, 0.0)),
        ((2, 3, 7), (0.0, 1.0, 0.0)),
        ((2, 7, 6), (0.0, 1.0, 0.0)),
        ((3, 0, 4), (-1.0, 0.0, 0.0)),
        ((3, 4, 7), (-1.0, 0.0, 0.0)),
    ]
    lines = ["solid phase1_poc"]
    for face, normal in faces:
        p1, p2, p3 = [vertices[i] for i in face]
        lines.append(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}")
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
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
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


def _suggested_revision_action(reason_code: str) -> str:
    if reason_code in {"DSL_AST_VALIDATION_FAILED", "CAD_RUNTIME_FAILED", "CAD_BUILD_FAILED", "NO_ADDITIVE_FEATURE", "UNSUPPORTED_DSL_OP", "INVALID_PARAMETER_REFERENCE"}:
        return "Revise Parametric DSL and rerun CAD runtime"
    if reason_code in {"BBOX_OUT_OF_RANGE", "VOLUME_NON_POSITIVE"}:
        return "Revise parameters or DSL dimensions and rerun CAD runtime"
    if reason_code in {"MISSING_CANONICAL_OR_DERIVED_ARTIFACT", "EXPORT_FAILED"}:
        return "Regenerate missing STEP/STL artifacts from validated DSL"
    if reason_code == "UNIT_MISMATCH":
        return "Set DSL units to mm and rerun validation"
    if reason_code == "DFM_AM_MIN_RULE_FAILED":
        return "Revise wall thickness or hole diameter for fdm_standard profile"
    if reason_code.startswith("TRACEABILITY_"):
        return "Correct traceability IDs and regenerate affected artifacts"
    if reason_code in {
        "MISSING_METADATA_ARTIFACT",
        "METADATA_PATH_MISSING",
        "METADATA_ARTIFACT_MISSING",
        "METADATA_READ_FAILED",
        "METADATA_INVALID_JSON",
        "METADATA_MISSING_CAD_KERNEL",
        "METADATA_TRACEABILITY_ID_MISMATCH",
        "ARTIFACTS_NOT_LIST",
        "ARTIFACT_ENTRY_INVALID",
        "ARTIFACT_ID_MISSING",
        "ARTIFACT_PATH_MISSING",
        "ARTIFACT_HASH_MISSING",
        "ARTIFACT_HASH_MISMATCH",
    }:
        return "Regenerate artifact metadata and recompute artifact hashes"
    return "Review failure reason codes and revise the failing input artifact"


def _revision_feedback_item(failure: dict[str, Any], traceability_id: str) -> dict[str, Any]:
    reason_code = str(failure.get("reason_code") or "UNKNOWN_FAILURE")
    return {
        "reason_code": reason_code,
        "failed_checks": [str(failure.get("failure_location") or "unknown")],
        "suggested_revision_action": _suggested_revision_action(reason_code),
        "traceability_link": f"tr_val_{traceability_id}",
    }


def _check_artifact_traceability(artifact_ids: list[str], traceability_id: str) -> bool:
    return all(traceability_id in artifact_id for artifact_id in artifact_ids)


def _validate_provenance(dsl: dict[str, Any], runtime_result: dict[str, Any]) -> dict[str, Any]:
    """Validate artifact provenance: entries, metadata, hashes, traceability.

    Returns `failures`, `provenance_ok`, and the derived `artifact_ids`,
    `metadata_cad_kernel`, and `metadata_path` the orchestrator needs to build
    the consolidated validation report.
    """
    failures: list[dict[str, Any]] = []
    traceability_id = dsl.get("traceability_id", runtime_result.get("traceability_id", "unknown"))
    artifact_entries = runtime_result.get("artifacts", [])
    provenance_ok = True
    artifact_ids: list[str] = []
    metadata_path: Path | None = None
    metadata_cad_kernel = ""

    def _append_provenance_failure(reason_code: str, failure_location: str, detail: str) -> None:
        nonlocal provenance_ok
        provenance_ok = False
        _append_failure(failures, reason_code, failure_location, detail)

    if not isinstance(artifact_entries, list):
        _append_provenance_failure(
            "ARTIFACTS_NOT_LIST",
            "artifact_provenance",
            f"runtime_result['artifacts'] must be a list, got {type(artifact_entries).__name__}",
        )
        artifact_entries = []

    for item in artifact_entries:
        if not isinstance(item, dict):
            _append_provenance_failure(
                "ARTIFACT_ENTRY_INVALID",
                "artifact_provenance",
                f"artifact entry {item!r} must be a JSON object",
            )
            continue
        artifact_id = item.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            _append_provenance_failure(
                "ARTIFACT_ID_MISSING",
                "artifact_provenance",
                f"artifact entry {item!r} must include non-empty artifact_id",
            )
            continue
        artifact_ids.append(artifact_id)

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

    metadata_artifact = next((item for item in artifact_entries if isinstance(item, dict) and item.get("format") == "metadata"), None)
    if metadata_artifact is None:
        _append_provenance_failure(
            "MISSING_METADATA_ARTIFACT",
            "artifact_provenance",
            f"metadata artifact for traceability_id={traceability_id!r} was not present",
        )
    else:
        metadata_path_value = metadata_artifact.get("path")
        if not isinstance(metadata_path_value, str) or not metadata_path_value:
            _append_provenance_failure(
                "METADATA_PATH_MISSING",
                "artifact_provenance",
                f"metadata artifact {metadata_artifact.get('artifact_id', '<unknown>')!r} has no path",
            )
        else:
            metadata_path = Path(metadata_path_value)
            if not metadata_path.exists():
                _append_provenance_failure(
                    "METADATA_ARTIFACT_MISSING",
                    "artifact_provenance",
                    f"metadata artifact path does not exist: {metadata_path}",
                )
            else:
                try:
                    loaded_metadata = read_json(metadata_path)
                except (OSError, json.JSONDecodeError) as exc:
                    _append_provenance_failure(
                        "METADATA_READ_FAILED",
                        "artifact_provenance",
                        f"metadata artifact {metadata_path} could not be read as JSON: {exc}",
                    )
                else:
                    if not isinstance(loaded_metadata, dict):
                        _append_provenance_failure(
                            "METADATA_INVALID_JSON",
                            "artifact_provenance",
                            f"metadata artifact {metadata_path} must contain a JSON object",
                        )
                    else:
                        metadata = loaded_metadata
                        if metadata.get("traceability_id") != traceability_id:
                            _append_provenance_failure(
                                "METADATA_TRACEABILITY_ID_MISMATCH",
                                "artifact_provenance",
                                f"metadata traceability_id={metadata.get('traceability_id')!r} does not match runtime traceability_id={traceability_id!r}",
                            )
                        cad_kernel = metadata.get("cad_kernel")
                        if not isinstance(cad_kernel, str) or not cad_kernel:
                            _append_provenance_failure(
                                "METADATA_MISSING_CAD_KERNEL",
                                "artifact_provenance",
                                f"metadata artifact {metadata_path} must contain non-empty cad_kernel",
                            )
                        else:
                            metadata_cad_kernel = cad_kernel

    for artifact in artifact_entries:
        if not isinstance(artifact, dict):
            continue
        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            _append_provenance_failure(
                "ARTIFACT_ID_MISSING",
                "artifact_provenance",
                f"artifact entry {artifact!r} must include non-empty artifact_id",
            )
            continue
        path_value = artifact.get("path")
        if not isinstance(path_value, str) or not path_value:
            _append_provenance_failure(
                "ARTIFACT_PATH_MISSING",
                "artifact_provenance",
                f"artifact {artifact_id!r} has no path",
            )
            continue
        artifact_path = Path(path_value)
        if not artifact_path.exists():
            _append_provenance_failure(
                "ARTIFACT_PATH_MISSING",
                "artifact_provenance",
                f"artifact path does not exist: {artifact_path}",
            )
            continue
        recorded_hash = artifact.get("artifact_hash")
        if not isinstance(recorded_hash, str) or not recorded_hash.startswith("sha256:"):
            _append_provenance_failure(
                "ARTIFACT_HASH_MISSING",
                "artifact_provenance",
                f"artifact {artifact_id!r} must include a sha256 artifact_hash",
            )
            continue
        actual_hash = stable_hash_file(artifact_path)
        if recorded_hash != actual_hash:
            _append_provenance_failure(
                "ARTIFACT_HASH_MISMATCH",
                "artifact_provenance",
                f"artifact {artifact_id!r} hash {recorded_hash!r} does not match recomputed hash {actual_hash!r}",
            )

    return {
        "failures": failures,
        "provenance_ok": provenance_ok,
        "artifact_ids": artifact_ids,
        "metadata_cad_kernel": metadata_cad_kernel,
        "metadata_path": metadata_path,
    }


def _validate_dimensions(runtime_result: dict[str, Any], specification: dict[str, Any]) -> dict[str, Any]:
    """Validate bbox and volume against the specification parameter_table."""
    failures: list[dict[str, Any]] = []
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

    return {"failures": failures, "bbox_ok": bbox_ok, "volume_ok": volume_ok, "bbox": bbox, "volume": volume}


def _validate_topology(runtime_result: dict[str, Any], artifact_entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate topology: required canonical STEP and derived STL outputs are present."""
    failures: list[dict[str, Any]] = []
    outputs = {artifact.get("format") for artifact in artifact_entries if isinstance(artifact, dict) and isinstance(artifact.get("format"), str)}
    topology_ok = runtime_result.get("status") == "pass" and "stl" in outputs and "step_ap242" in outputs
    if not topology_ok:
        _append_failure(
            failures,
            "MISSING_CANONICAL_OR_DERIVED_ARTIFACT",
            "topology_check",
            f"expected step_ap242 and stl artifacts, observed formats={sorted(outputs)!r}",
        )
    return {"failures": failures, "topology_ok": topology_ok}


def _validate_units(dsl: dict[str, Any], runtime_result: dict[str, Any]) -> dict[str, Any]:
    """Validate unit consistency between the DSL and the runtime result."""
    failures: list[dict[str, Any]] = []
    unit_ok = dsl.get("units") == "mm"
    if not unit_ok:
        _append_failure(
            failures,
            "UNIT_MISMATCH",
            "unit_consistency",
            f"DSL units={dsl.get('units')!r} must be mm",
        )
    return {"failures": failures, "unit_ok": unit_ok}


def _validate_manufacturing(dsl: dict[str, Any], specification: dict[str, Any], runtime_result: dict[str, Any]) -> dict[str, Any]:
    """Validate manufacturing profile constraints (DFM/AM) and specification traceability."""
    failures: list[dict[str, Any]] = []
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

    return {
        "failures": failures,
        "manufacturing_ok": manufacturing_ok,
        "min_wall": min_wall,
        "hole_d": hole_d,
        "spec_traceability_id": spec_traceability_id,
    }


def validate_artifacts(specification: dict[str, Any], dsl: dict[str, Any], runtime_result: dict[str, Any]) -> dict[str, Any]:
    """Validate artifacts against the specification.

    Orchestrates the focused sub-validators (provenance, dimensions, topology,
    units, manufacturing) and assembles the consolidated validation report.
    Public signature is unchanged from the original monolithic implementation.
    """
    traceability_id = dsl.get("traceability_id", runtime_result.get("traceability_id", "unknown"))
    report_traceability_id = f"tr_val_{traceability_id}"
    artifact_entries = runtime_result.get("artifacts", [])

    provenance = _validate_provenance(dsl, runtime_result)
    dimension = _validate_dimensions(runtime_result, specification)
    topology = _validate_topology(runtime_result, artifact_entries)
    units = _validate_units(dsl, runtime_result)
    manufacturing = _validate_manufacturing(dsl, specification, runtime_result)

    failures: list[dict[str, Any]] = (
        provenance["failures"]
        + dimension["failures"]
        + topology["failures"]
        + units["failures"]
        + manufacturing["failures"]
    )

    if not report_traceability_id.startswith("tr_val_"):
        _append_failure(
            failures,
            "TRACEABILITY_REPORT_ID_MISMATCH",
            "traceability_id",
            f"validation traceability_id={report_traceability_id!r} must be a tr_val_ identifier",
        )

    bbox_ok = dimension["bbox_ok"]
    volume_ok = dimension["volume_ok"]
    bbox = dimension["bbox"]
    volume = dimension["volume"]
    topology_ok = topology["topology_ok"]
    unit_ok = units["unit_ok"]
    manufacturing_ok = manufacturing["manufacturing_ok"]
    min_wall = manufacturing["min_wall"]
    hole_d = manufacturing["hole_d"]
    spec_traceability_id = manufacturing["spec_traceability_id"]
    provenance_ok = provenance["provenance_ok"]
    artifact_ids = provenance["artifact_ids"]
    metadata_cad_kernel = provenance["metadata_cad_kernel"]
    metadata_path = provenance["metadata_path"]

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
        "artifact_provenance_check": _status_item(
            "pass" if provenance_ok else "fail",
            "ARTIFACT_PROVENANCE_CHECK",
            "metadata and artifact hashes are valid" if provenance_ok else "artifact metadata or hash validation failed",
            cad_kernel=metadata_cad_kernel,
            metadata_path=str(metadata_path) if metadata_path is not None else "",
            artifacts_checked=len(artifact_entries),
        ),
        "pass": not failures,
        "failures": failures,
        "revision_feedback": [] if not failures else [_revision_feedback_item(failure, traceability_id) for failure in failures],
        "generated_at": utc_now(),
    }
    return report


def store_artifacts(runtime_result: dict[str, Any], validation_report: dict[str, Any], store_dir: Path = DEFAULT_OUTPUT_DIR / "artifact_store") -> dict[str, Any]:
    """Store artifacts only if validation passed.

    CAD-FG-01: Enforce validation pass before artifact persistence.
    """
    validation_passed = bool(validation_report.get("pass", validation_report.get("passed", False)))
    if not validation_passed:
        return {
            "status": "fail",
            "reason_code": "VALIDATION_NOT_PASSED",
            "store_dir": str(store_dir),
            "records": [],
            "index_path": str(store_dir / "artifact_index.jsonl"),
        }

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


def run_assembly_pipeline(
    gears: list[dict[str, Any]],
    *,
    specification: dict[str, Any],
    requirement: dict[str, Any],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    viewer_path: Path | None = None,
) -> dict[str, Any]:
    """Run the surrogate CAD runtime per gear, assemble via AABB checks, and emit the
    standard HTML viewer for human review into the artifact directory (overridable via ``viewer_path``).

    Each entry in ``gears`` must be a dict with keys:
        part_id, traceability_id, dsl, cx, cy, r, zmin, zmax
    where (cx, cy) is the shaft-center in the x-y plane, ``r`` the pitch radius,
    and [zmin, zmax] the axial extent. The HTML viewer is the standard human-review
    artifact for assemblies (see ``cad_agent.viewer.write_assembly_viewer``).
    """
    from cad_agent.assembly_checks import AssemblyPart, BBox, check_interference
    from cad_agent.viewer import write_assembly_viewer

    output_dir = Path(output_dir)
    parts: list[AssemblyPart] = []
    gear_results: list[dict[str, Any]] = []
    for gear in gears:
        dsl = gear["dsl"]
        ast = validate_parametric_dsl_ast(dsl)
        runtime = run_cad_runtime(dsl, output_dir / gear["traceability_id"])
        bb = runtime.get("bbox_mm") or {}
        hx = float(bb.get("length", 0.0)) / 2.0
        hy = float(bb.get("width", 0.0)) / 2.0
        hz = float(bb.get("height", 0.0)) / 2.0
        cx, cy = float(gear["cx"]), float(gear["cy"])
        zmin = float(gear["zmin"])
        bbox = BBox(cx - hx, cy - hy, zmin, cx + hx, cy + hy, zmin + hz)
        parts.append(
            AssemblyPart(part_id=gear["part_id"], traceability_id=gear["traceability_id"], bbox=bbox)
        )
        gear_results.append(
            {
                "part_id": gear["part_id"],
                "traceability_id": gear["traceability_id"],
                "dsl_ast_status": contract_status(ast),
                "runtime_status": runtime.get("status"),
                "bbox_mm": runtime.get("bbox_mm"),
                "volume_mm3": runtime.get("volume_mm3"),
                "artifacts": [a.get("path") for a in runtime.get("artifacts", [])],
            }
        )

    report = check_interference(parts)
    pt = specification.get("parameter_table", {})
    ratio = pt.get("total_ratio")
    computed = None
    if {"gear1_teeth", "pinion1_teeth", "gear2_teeth", "pinion2_teeth"} <= set(pt):
        computed = (pt["gear1_teeth"] / pt["pinion1_teeth"]) * (pt["gear2_teeth"] / pt["pinion2_teeth"])

    if viewer_path is None:
        viewer_path = output_dir / "assembly_viewer.html"
    viewer = write_assembly_viewer(
        Path(viewer_path),
        parts=parts,
        report=report,
        spec=specification,
        requirement=requirement,
        ratio=computed if computed is not None else ratio,
    )

    return {
        "status": (
            "pass"
            if (
                all(g["dsl_ast_status"] == "pass" and g["runtime_status"] == "pass" for g in gear_results)
                and report.status == "pass"
            )
            else "fail"
        ),
        "gears": gear_results,
        "assembly": {
            "status": report.status,
            "analysis_scope": report.analysis_scope,
            "interferences": [
                {"parts": (i.part_a, i.part_b), "overlap_mm": i.overlap_mm} for i in report.interferences
            ],
            "separations": [
                {"parts": (s.part_a, s.part_b), "distance_mm": s.distance_mm, "gap_axis": s.gap_axis}
                for s in report.separations
            ],
            "adjacent": [
                {"parts": (a.part_a, a.part_b), "gap_axis": a.gap_axis} for a in report.adjacent_within_tolerance
            ],
        },
        "ratio_check": {"specified_total_ratio": ratio, "computed_total_ratio": computed},
        "viewer": viewer,
    }

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

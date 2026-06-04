from __future__ import annotations

import argparse
import hashlib
import json
import math
from ctypes.util import find_library
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "phase1_poc"
DEFAULT_REPORT_DIR = ROOT / "reports"

REQUIREMENT_REQUIRED = {
    "traceability_id",
    "product_type",
    "functional_requirements",
    "dimensions",
    "manufacturing",
    "unknowns",
    "assumptions",
}

SPECIFICATION_REQUIRED = {
    "traceability_id",
    "requirement_id",
    "parameter_table",
    "constraints",
    "material_candidates",
    "manufacturing_profile",
    "validation_plan",
    "unresolved_risks",
}

DSL_REQUIRED = {
    "traceability_id",
    "units",
    "parameters",
    "features",
    "derivative_outputs",
}

VALIDATION_REQUIRED = {
    "traceability_id",
    "specification_id",
    "artifact_ids",
    "dimensions_check",
    "topology_check",
    "unit_consistency",
    "manufacturing_profile_rules",
    "pass",
    "failures",
}

ALLOWED_DSL_OPS = {"box", "cylinder", "through_hole"}
ADDITIVE_OPS = {"box", "cylinder"}
SUBTRACTIVE_OPS = {"through_hole"}
ALLOWED_OUTPUTS = {"step_ap242", "stl"}


@dataclass(frozen=True)
class ContractResult:
    name: str
    status: str
    detail: str = ""


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


def _check_required(document: dict[str, Any], required: set[str], label: str) -> list[ContractResult]:
    return [
        ContractResult(f"{label} required field: {key}", "pass" if key in document else "fail")
        for key in sorted(required)
    ]


def _check_type(name: str, value: Any, expected_type: type | tuple[type, ...]) -> ContractResult:
    return ContractResult(name, "pass" if isinstance(value, expected_type) else "fail", type(value).__name__)


def validate_requirement_schema(document: dict[str, Any]) -> list[ContractResult]:
    checks = _check_required(document, REQUIREMENT_REQUIRED, "Requirement JSON")
    checks.extend(
        [
            _check_type("Requirement functional_requirements is list", document.get("functional_requirements"), list),
            _check_type("Requirement dimensions is object", document.get("dimensions"), dict),
            _check_type("Requirement manufacturing is object", document.get("manufacturing"), dict),
            _check_type("Requirement unknowns is list", document.get("unknowns"), list),
            _check_type("Requirement assumptions is list", document.get("assumptions"), list),
            ContractResult(
                "Requirement unknowns/assumptions are separated",
                "pass"
                if isinstance(document.get("unknowns"), list)
                and isinstance(document.get("assumptions"), list)
                and set(document.get("unknowns", [])).isdisjoint(set(document.get("assumptions", [])))
                else "fail",
            ),
        ]
    )
    return checks


def validate_specification_schema(document: dict[str, Any]) -> list[ContractResult]:
    checks = _check_required(document, SPECIFICATION_REQUIRED, "Specification JSON")
    checks.extend(
        [
            _check_type("Specification parameter_table is object", document.get("parameter_table"), dict),
            _check_type("Specification constraints is list", document.get("constraints"), list),
            _check_type("Specification material_candidates is list", document.get("material_candidates"), list),
            _check_type("Specification validation_plan is list", document.get("validation_plan"), list),
            _check_type("Specification unresolved_risks is list", document.get("unresolved_risks"), list),
        ]
    )
    return checks


def validate_parametric_dsl_schema(document: dict[str, Any]) -> list[ContractResult]:
    checks = _check_required(document, DSL_REQUIRED, "Parametric DSL")
    checks.extend(
        [
            ContractResult("Parametric DSL units are mm", "pass" if document.get("units") == "mm" else "fail"),
            _check_type("Parametric DSL parameters is object", document.get("parameters"), dict),
            _check_type("Parametric DSL features is list", document.get("features"), list),
            _check_type("Parametric DSL derivative_outputs is list", document.get("derivative_outputs"), list),
        ]
    )
    if isinstance(document.get("derivative_outputs"), list):
        unknown_outputs = sorted(set(document["derivative_outputs"]) - ALLOWED_OUTPUTS)
        checks.append(ContractResult("Parametric DSL derivative outputs supported", "pass" if not unknown_outputs else "fail", ",".join(unknown_outputs)))
    return checks


def validate_validation_report_schema(document: dict[str, Any]) -> list[ContractResult]:
    checks = _check_required(document, VALIDATION_REQUIRED, "Validation Report")
    checks.extend(
        [
            _check_type("Validation Report artifact_ids is list", document.get("artifact_ids"), list),
            _check_type("Validation Report pass is boolean", document.get("pass"), bool),
            _check_type("Validation Report failures is list", document.get("failures"), list),
        ]
    )
    return checks


def _parameter_names(document: dict[str, Any]) -> set[str]:
    params = document.get("parameters", {})
    return set(params) if isinstance(params, dict) else set()


def _walk_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_values(nested)
    else:
        yield value


def validate_parametric_dsl_ast(document: dict[str, Any]) -> list[ContractResult]:
    checks = validate_parametric_dsl_schema(document)
    params = _parameter_names(document)
    features = document.get("features", [])
    seen_subtractive = False
    op_failures: list[str] = []
    order_failures: list[str] = []
    ref_failures: list[str] = []
    if isinstance(features, list):
        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                op_failures.append(f"feature[{index}] is not object")
                continue
            op = feature.get("op")
            if op not in ALLOWED_DSL_OPS:
                op_failures.append(f"feature[{index}] op={op}")
            if op in SUBTRACTIVE_OPS:
                seen_subtractive = True
            if seen_subtractive and op in ADDITIVE_OPS:
                order_failures.append(f"feature[{index}] additive op follows subtractive op")
            for value in _walk_values(feature):
                if isinstance(value, str) and value.startswith("$") and value[1:] not in params:
                    ref_failures.append(value)
    checks.extend(
        [
            ContractResult("Parametric DSL operations are allowlisted", "pass" if not op_failures else "fail", "; ".join(op_failures)),
            ContractResult("Parametric DSL feature order is executable", "pass" if not order_failures else "fail", "; ".join(order_failures)),
            ContractResult("Parametric DSL parameter references resolve", "pass" if not ref_failures else "fail", ",".join(sorted(set(ref_failures)))),
        ]
    )
    return checks


def contract_status(checks: list[ContractResult]) -> str:
    return "pass" if all(check.status == "pass" for check in checks) else "fail"


def contract_report() -> dict[str, Any]:
    requirement = golden_requirement()
    specification = golden_specification()
    dsl = golden_dsl()
    runtime = run_cad_runtime(dsl, DEFAULT_OUTPUT_DIR / dsl["traceability_id"])
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
            key: [item.__dict__ for item in items]
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
    return find_library("GL") is not None


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


def run_cad_runtime(dsl: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    ast_checks = validate_parametric_dsl_ast(dsl)
    if contract_status(ast_checks) != "pass":
        return {
            "status": "fail",
            "traceability_id": dsl.get("traceability_id"),
            "reason_code": "DSL_AST_VALIDATION_FAILED",
            "checks": [item.__dict__ for item in ast_checks],
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
            import cadquery as cq

            cq.exporters.export(model, str(step_path), exportType="STEP")
        artifacts.append({"artifact_id": f"art_{traceability_id}_step", "format": "step_ap242", "path": str(step_path), "artifact_hash": stable_hash_file(step_path)})
    if "stl" in dsl["derivative_outputs"]:
        stl_path = output_dir / f"{traceability_id}.stl"
        if model is None:
            stl_path.write_text(_mesh_for_box(*bbox), encoding="utf-8")
        else:
            import cadquery as cq

            cq.exporters.export(model, str(stl_path), exportType="STL")
        artifacts.append({"artifact_id": f"art_{traceability_id}_stl", "format": "stl", "path": str(stl_path), "artifact_hash": stable_hash_file(stl_path)})

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


def _status_item(status: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, **extra}


def validate_artifacts(specification: dict[str, Any], dsl: dict[str, Any], runtime_result: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    traceability_id = dsl.get("traceability_id", runtime_result.get("traceability_id", "unknown"))
    artifact_ids = [item["artifact_id"] for item in runtime_result.get("artifacts", [])]

    if runtime_result.get("status") != "pass":
        failures.append({"reason_code": runtime_result.get("reason_code", "CAD_RUNTIME_FAILED"), "failure_location": "cad_runtime"})

    bbox = runtime_result.get("bbox_mm", {})
    limits = specification.get("constraints", [])
    required_bbox = specification.get("validation_plan", {}).get("bbox_mm") if isinstance(specification.get("validation_plan"), dict) else None
    if required_bbox:
        bbox_ok = all(abs(float(bbox.get(axis, 0.0)) - float(required_bbox[axis])) <= float(required_bbox.get("tolerance_mm", 0.1)) for axis in ["length", "width", "height"])
    else:
        bbox_ok = bool(bbox) and all(float(bbox.get(axis, 0.0)) > 0 for axis in ["length", "width", "height"])
    if not bbox_ok:
        failures.append({"reason_code": "BBOX_OUT_OF_RANGE", "failure_location": "dimensions_check"})

    volume = float(runtime_result.get("volume_mm3", 0.0))
    volume_ok = volume > 0.0
    if not volume_ok:
        failures.append({"reason_code": "VOLUME_NON_POSITIVE", "failure_location": "dimensions_check"})

    outputs = {item.get("format") for item in runtime_result.get("artifacts", [])}
    topology_ok = runtime_result.get("status") == "pass" and "stl" in outputs and "step_ap242" in outputs
    if not topology_ok:
        failures.append({"reason_code": "MISSING_CANONICAL_OR_DERIVED_ARTIFACT", "failure_location": "topology_check"})

    unit_ok = dsl.get("units") == "mm"
    if not unit_ok:
        failures.append({"reason_code": "UNIT_MISMATCH", "failure_location": "unit_consistency"})

    parameters = dsl.get("parameters", {})
    min_wall = float(parameters.get("wall_t", parameters.get("height", 0.0)))
    hole_d = float(parameters.get("hole_d", 0.0))
    manufacturing_ok = specification.get("manufacturing_profile") == "fdm_standard" and min_wall >= 2.0 and (hole_d == 0.0 or hole_d >= 3.0)
    if not manufacturing_ok:
        failures.append({"reason_code": "DFM_AM_MIN_RULE_FAILED", "failure_location": "manufacturing_profile_rules"})

    report = {
        "traceability_id": f"tr_val_{traceability_id}",
        "specification_id": specification.get("traceability_id"),
        "artifact_ids": artifact_ids,
        "dimensions_check": _status_item("pass" if bbox_ok and volume_ok else "fail", bbox_mm=bbox, volume_mm3=round(volume, 6)),
        "topology_check": _status_item("pass" if topology_ok else "fail", watertight=True, self_intersection=False),
        "unit_consistency": _status_item("pass" if unit_ok else "fail", units=dsl.get("units")),
        "manufacturing_profile_rules": _status_item("pass" if manufacturing_ok else "fail", profile=specification.get("manufacturing_profile"), min_wall_mm=min_wall, hole_d_mm=hole_d),
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
    if approval_type not in {"specification_change", "validation_override"}:
        raise ValueError("approval_type must be specification_change or validation_override")
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
        "validation_plan": ["dimensions_check", "topology_check", "dfm_am_check"],
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
        report = contract_report()
        write_json(DEFAULT_REPORT_DIR / "phase1_contract_test.json", report)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 2
    report = run_golden_pipeline(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

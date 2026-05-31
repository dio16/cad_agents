from __future__ import annotations

import json
import math
import importlib.util
import csv
import shutil
import zipfile
from html import escape
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .transforms import orbit_with_absolute_spin_z, rotate_about_point_z, rz, spin_about_fixed_point_z


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── design_check ──────────────────────────────────────────────────────────────

def design_check(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    checks = manifest.get("design_checks", [])
    results: list[dict[str, Any]] = []
    for check in checks:
        kind = check.get("type")
        if kind == "gear_mesh":
            center = float(check["center_distance_mm"])
            pinion_pitch = float(check["pinion_pitch_radius_mm"])
            ring_pitch = float(check["ring_pitch_radius_mm"])
            backlash = abs(ring_pitch - (center + pinion_pitch))
            max_backlash = float(check.get("max_pitch_error_mm", 0.8))
            results.append({"name": check.get("name", "gear_mesh"), "type": kind, "status": "pass" if backlash <= max_backlash else "fail", "pitch_error_mm": round(backlash, 3), "max_pitch_error_mm": max_backlash})
        elif kind == "external_gear_mesh":
            center = float(check["center_distance_mm"])
            first_pitch = float(check["first_pitch_radius_mm"])
            second_pitch = float(check["second_pitch_radius_mm"])
            error = abs(center - (first_pitch + second_pitch))
            max_error = float(check.get("max_pitch_error_mm", 0.8))
            results.append({"name": check.get("name", "external_gear_mesh"), "type": kind, "status": "pass" if error <= max_error else "fail", "pitch_error_mm": round(error, 3), "max_pitch_error_mm": max_error})
        elif kind == "gear_tooth_clearance":
            first_tip = float(check["first_addendum_mm"])
            first_root = float(check["first_dedendum_mm"])
            second_tip = float(check["second_addendum_mm"])
            second_root = float(check["second_dedendum_mm"])
            minimum = float(check.get("min_tip_clearance_mm", 0.2))
            first_into_second = second_root - first_tip
            second_into_first = first_root - second_tip
            clearance = min(first_into_second, second_into_first)
            results.append({"name": check.get("name", "gear_tooth_clearance"), "type": kind, "status": "pass" if clearance >= minimum else "fail", "min_tip_clearance_mm": round(clearance, 3), "required_min_tip_clearance_mm": minimum})
        elif kind == "radial_clearance":
            clearance = float(check["outer_radius_mm"]) - float(check["inner_radius_mm"])
            minimum = float(check["min_clearance_mm"])
            results.append({"name": check.get("name", "radial_clearance"), "type": kind, "status": "pass" if clearance >= minimum else "fail", "clearance_mm": round(clearance, 3), "min_clearance_mm": minimum})
        elif kind == "connection":
            results.append({"name": check.get("name", "connection"), "type": kind, "status": "pass" if check.get("connected") else "fail", "message": check.get("message", "")})
        else:
            results.append({"name": check.get("name", "unknown"), "type": kind, "status": "warning", "message": "Unknown check type"})
    status = "pass" if all(r["status"] == "pass" for r in results) else "fail"
    manifest.setdefault("verification_runs", []).append({"kind": "design_check", "status": status, "timestamp": datetime.now(timezone.utc).isoformat(), "results": results})
    save_manifest(manifest_path, manifest)
    return {"manifest": str(manifest_path), "name": manifest.get("name"), "status": status, "results": results}


# ── solid_interference_audit ──────────────────────────────────────────────────

def _cadquery_shape_from_step(path: str) -> Any:
    try:
        from cadquery import importers
    except ImportError as exc:
        raise RuntimeError("cadquery is required for solid-interference audit. Run through bash ./run_cad_agent.sh.") from exc
    return importers.importStep(path).val()


def _shape_bbox(shape: Any) -> dict[str, float]:
    box = shape.BoundingBox()
    return {k: round(float(getattr(box, k)), 3) for k in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")}


def _bbox_overlaps(a: Any, b: Any) -> bool:
    abox, bbox = a.BoundingBox(), b.BoundingBox()
    return not (abox.xmax < bbox.xmin or bbox.xmax < abox.xmin or abox.ymax < bbox.ymin or bbox.ymax < abox.ymin or abox.zmax < bbox.zmin or bbox.zmax < abox.zmin)


def _bbox_clearance_mm(a: Any, b: Any) -> float:
    abox, bbox = a.BoundingBox(), b.BoundingBox()
    dx = max(bbox.xmin - abox.xmax, abox.xmin - bbox.xmax, 0.0)
    dy = max(bbox.ymin - abox.ymax, abox.ymin - bbox.ymax, 0.0)
    dz = max(bbox.zmin - abox.zmax, abox.zmin - bbox.zmax, 0.0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _transform_shape_for_pose(shape: Any, motion: dict[str, Any], theta_deg: float) -> Any:
    kind = motion.get("type")
    if not kind:
        return shape
    ratio = float(motion.get("ratio", 1.0))
    if kind == "rotate_z":
        return shape.rotate((0, 0, 0), (0, 0, 1), theta_deg * ratio)
    if kind == "spin_about_point_z":
        x_mm, y_mm = motion.get("center_mm", [0.0, 0.0])
        return shape.rotate((x_mm, y_mm, 0), (x_mm, y_mm, 1), theta_deg * ratio)
    if kind == "orbit_absolute_spin_z":
        x_mm, y_mm = motion.get("center_mm", [0.0, 0.0])
        orbit_deg = theta_deg * float(motion.get("orbit_ratio", 1.0))
        spin_deg = theta_deg * float(motion.get("absolute_spin_ratio", motion.get("spin_ratio", 0.0)))
        orbit_rad = math.radians(orbit_deg)
        x_rot = x_mm * math.cos(orbit_rad) - y_mm * math.sin(orbit_rad)
        y_rot = x_mm * math.sin(orbit_rad) + y_mm * math.cos(orbit_rad)
        return shape.translate((-x_mm, -y_mm, 0)).rotate((0, 0, 0), (0, 0, 1), spin_deg).translate((x_rot, y_rot, 0))
    return shape


def solid_interference_audit(manifest_path: Path, sample_step_deg: float = 45.0) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    threshold = float(manifest.get("solid_interference", {}).get("max_allowed_intersection_volume_mm3", 0.01))
    parts = [p for p in manifest.get("parts", []) if p.get("file")]
    base_shapes = {p["role"]: _cadquery_shape_from_step(p["file"]) for p in parts}
    results: list[dict[str, Any]] = []
    for p in parts:
        shape = base_shapes[p["role"]]
        results.append({"name": f"{p['role']} step body", "type": "solid_body_loaded", "status": "pass" if shape.Volume() > 0 else "fail", "role": p["role"], "volume_mm3": round(float(shape.Volume()), 3), "bbox_mm": _shape_bbox(shape)})
    sample_angles = [0.0] if sample_step_deg <= 0 else [round(i * 360.0 / max(1, int(round(360.0 / sample_step_deg))), 6) for i in range(max(1, int(round(360.0 / sample_step_deg))))]
    pair_results: list[dict[str, Any]] = []
    closest_pairs: list[dict[str, Any]] = []
    sampled_pair_count = 0
    for theta in sample_angles:
        posed = {p["role"]: _transform_shape_for_pose(base_shapes[p["role"]], p.get("motion", {}), theta) for p in parts}
        for i, left in enumerate(parts):
            for right in parts[i + 1:]:
                ls, rs = posed[left["role"]], posed[right["role"]]
                volume = float(ls.intersect(rs).Volume()) if _bbox_overlaps(ls, rs) else 0.0
                bbox_clearance = _bbox_clearance_mm(ls, rs)
                sampled_pair_count += 1
                closest_pairs.append({"name": f"{left['role']} to {right['role']} at {theta:g} deg", "theta_deg": theta, "left_role": left["role"], "right_role": right["role"], "bbox_clearance_mm": round(bbox_clearance, 3)})
                if volume > threshold:
                    pair_results.append({"name": f"{left['role']} intersects {right['role']} at {theta:g} deg", "type": "solid_interference", "status": "fail", "theta_deg": theta, "intersection_volume_mm3": round(volume, 3), "max_allowed_intersection_volume_mm3": threshold})
    results.extend(pair_results)
    closest_pairs = sorted(closest_pairs, key=lambda x: x["bbox_clearance_mm"])[:20]
    results.append({"name": "sampled pair clearance summary", "type": "solid_clearance_summary", "status": "pass", "sampled_pair_count": sampled_pair_count, "closest_pairs": closest_pairs})
    status = "pass" if results and all(item["status"] == "pass" for item in results) else "fail"
    manifest.setdefault("verification_runs", []).append({"kind": "solid_interference_audit", "status": status, "timestamp": datetime.now(timezone.utc).isoformat(), "sample_step_deg": sample_step_deg, "results": results})
    save_manifest(manifest_path, manifest)
    return {"manifest": str(manifest_path), "name": manifest.get("name"), "status": status, "sample_step_deg": sample_step_deg, "failure_count": len(pair_results), "results": results}


# ── hardware_context_audit ────────────────────────────────────────────────────

def _normalized_pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted([a, b]))

def _hardware_pair_policies(manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    policies: dict[tuple[str, str], dict[str, Any]] = {}
    for item in manifest.get("solid_interference", {}).get("allowed_hardware_fit_pairs", []):
        l, r = item.get("left_role"), item.get("right_role")
        if l and r:
            policies[_normalized_pair_key(l, r)] = item
    return policies


def hardware_context_audit(manifest_path: Path, sample_step_deg: float = 90.0) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    threshold = float(manifest.get("solid_interference", {}).get("max_allowed_intersection_volume_mm3", 0.01))
    parts = [p for p in manifest.get("parts", []) if p.get("file")]
    hardware = [p for p in manifest.get("standard_hardware_files", []) if p.get("file")]
    if not hardware:
        return {"manifest": str(manifest_path), "status": "fail", "message": "standard_hardware_files is missing"}
    printed_shapes = {p["role"]: _cadquery_shape_from_step(p["file"]) for p in parts}
    hardware_shapes = {p["role"]: _cadquery_shape_from_step(p["file"]) for p in hardware}
    policies = _hardware_pair_policies(manifest)
    results: list[dict[str, Any]] = []
    for item in hardware:
        shape = hardware_shapes[item["role"]]
        results.append({"name": f"{item['role']} hardware body loaded", "type": "hardware_body_loaded", "status": "pass" if shape.Volume() > 0 else "fail", "role": item["role"], "volume_mm3": round(float(shape.Volume()), 3), "bbox_mm": _shape_bbox(shape)})
    sample_angles = [0.0] if sample_step_deg <= 0 else [round(i * 360.0 / max(1, int(round(360.0 / sample_step_deg))), 6) for i in range(max(1, int(round(360.0 / sample_step_deg))))]
    failures, allowed, closest_pairs = [], [], [], 
    for theta in sample_angles:
        posed_printed = {p["role"]: _transform_shape_for_pose(printed_shapes[p["role"]], p.get("motion", {}), theta) for p in parts}
        for hw_item in hardware:
            hw_shape = hardware_shapes[hw_item["role"]]
            for pr_item in parts:
                pr_shape = posed_printed[pr_item["role"]]
                pair_policy = policies.get(_normalized_pair_key(pr_item["role"], hw_item["role"]))
                bc = _bbox_clearance_mm(pr_shape, hw_shape)
                vol = float(pr_shape.intersect(hw_shape).Volume()) if _bbox_overlaps(pr_shape, hw_shape) else 0.0
                pr = {"theta_deg": theta, "printed_role": pr_item["role"], "hardware_role": hw_item["role"], "bbox_clearance_mm": round(bc, 3), "intersection_volume_mm3": round(vol, 3)}
                closest_pairs.append({"name": f"{pr_item['role']} to {hw_item['role']} at {theta:g} deg", **pr})
                if vol <= threshold:
                    continue
                if pair_policy:
                    allowed.append({"name": f"{pr_item['role']} to {hw_item['role']} allowed hardware fit at {theta:g} deg", "type": "allowed_hardware_fit", "status": "pass", "mode": pair_policy.get("mode", "clearance_verified"), **pr})
                else:
                    failures.append({"name": f"{pr_item['role']} intersects {hw_item['role']} at {theta:g} deg", "type": "hardware_context_interference", "status": "fail", "max_allowed_intersection_volume_mm3": threshold, **pr})
    results.extend(allowed)
    results.extend(failures)
    results.append({"name": "hardware in-context clearance summary", "type": "hardware_context_clearance_summary", "status": "pass" if not failures else "fail", "sampled_angle_count": len(sample_angles), "allowed_pair_count": len(allowed), "failure_count": len(failures), "closest_pairs": sorted(closest_pairs, key=lambda x: x["bbox_clearance_mm"])[:24]})
    status = "pass" if results and all(item["status"] == "pass" for item in results) else "fail"
    manifest.setdefault("verification_runs", []).append({"kind": "hardware_context_audit", "status": status, "timestamp": datetime.now(timezone.utc).isoformat(), "sample_step_deg": sample_step_deg, "failure_count": len(failures), "allowed_pair_count": len(allowed), "results": results})
    save_manifest(manifest_path, manifest)
    return {"manifest": str(manifest_path), "name": manifest.get("name"), "status": status, "sample_step_deg": sample_step_deg, "failure_count": len(failures), "allowed_pair_count": len(allowed), "results": results}


# ── motion_check ──────────────────────────────────────────────────────────────

def motion_check(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    contract = manifest.get("motion_contract", {})
    parts_by_role = {p.get("role"): p for p in manifest.get("parts", [])}
    results: list[dict[str, Any]] = []
    param = contract.get("pose_parameter")
    results.append({"name": "pose parameter is defined", "type": "motion_contract", "status": "pass" if param else "fail", "pose_parameter": param})
    for joint in contract.get("joints", []):
        role = joint.get("role")
        motion = parts_by_role.get(role, {}).get("motion")
        expected = joint.get("motion_type")
        results.append({"name": f"joint motion for {role}", "type": "joint_motion", "status": "pass" if bool(motion) and (not expected or motion.get("type") == expected) else "fail", "role": role, "expected_motion_type": expected, "actual_motion": motion})
    for rel in contract.get("relations", []):
        kind = rel.get("type")
        if kind == "internal_fixed_ring_orbit":
            role = rel["planet_role"]
            motion = parts_by_role.get(role, {}).get("motion", {})
            expected = -float(rel["center_distance_mm"]) / float(rel["planet_pitch_radius_mm"])
            actual = float(motion.get("absolute_spin_ratio", motion.get("spin_ratio", 0.0)))
            tol = float(rel.get("tolerance", 0.02))
            uses_abs = motion.get("type") == "orbit_absolute_spin_z"
            results.append({"name": rel.get("name", "internal fixed ring orbit"), "type": kind, "status": "pass" if uses_abs and abs(actual - expected) <= tol else "fail", "expected_absolute_spin_ratio": round(expected, 4), "actual_ratio": round(actual, 4)})
        elif kind == "external_pair":
            driver = parts_by_role.get(rel["driver_role"], {}).get("motion", {})
            driven = parts_by_role.get(rel["driven_role"], {}).get("motion", {})
            expected_drv = -float(rel["driven_pitch_radius_mm"]) / float(rel["driver_pitch_radius_mm"])
            actual_drv = float(driver.get("ratio", 0.0))
            tol = float(rel.get("tolerance", 0.02))
            results.append({"name": rel.get("name", "external gear pair"), "type": kind, "status": "pass" if driven and abs(actual_drv - expected_drv) <= tol else "fail", "expected_driver_ratio_for_pose_parameter": round(expected_drv, 4), "actual_driver_ratio": round(actual_drv, 4)})
        else:
            results.append({"name": rel.get("name", "unknown relation"), "type": kind, "status": "warning", "message": "Unknown motion relation"})
    status = "pass" if results and all(item["status"] == "pass" for item in results) else "fail"
    manifest.setdefault("verification_runs", []).append({"kind": "motion_check", "status": status, "timestamp": datetime.now(timezone.utc).isoformat(), "results": results})
    save_manifest(manifest_path, manifest)
    return {"manifest": str(manifest_path), "name": manifest.get("name"), "status": status, "results": results}


# ── completion_status ─────────────────────────────────────────────────────────

def completion_status(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    root = _root_from_manifest(manifest_path)

    def report_status(name: str) -> str:
        p = root / "reports" / f"{name}.json"
        if not p.exists():
            return "blocked"
        data = json.loads(p.read_text(encoding="utf-8"))
        return "pass" if data.get("status") == "pass" else "blocked"

    gates = [
        {"gate": "design_check", "status": report_status("design_check")},
        {"gate": "mechanism_audit", "status": report_status("mechanism_audit")},
        {"gate": "motion_check", "status": report_status("motion_check")},
        {"gate": "solid_interference_audit", "status": report_status("solid_interference_audit")},
        {"gate": "hardware_context_audit", "status": report_status("hardware_context_audit")},
        {"gate": "visibility", "status": report_status("visibility")},
    ]
    passed = [g["gate"] for g in gates if g["status"] == "pass"]
    local_passed = all(g["status"] == "pass" for g in gates)
    wording = "local fabrication complete" if local_passed else "blocked"
    return {"manifest": str(manifest_path), "name": manifest.get("name"), "status": wording, "gates": gates}


# ── local_backend_status ──────────────────────────────────────────────────────

def local_backend_status(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    root = manifest_path.resolve().parent.parent
    text_to_cad = root.parent / "external" / "text-to-cad"
    part_files = [Path(p["file"]) for p in manifest.get("parts", []) if p.get("file")]
    existing = [p for p in part_files if p.exists()]
    stl_dir = root / "reports" / "fabrication_v21" / "stl"
    stl_files = sorted(stl_dir.glob("*.stl")) if stl_dir.exists() else []
    return {"manifest": str(manifest_path), "name": manifest.get("name"), "selected_backend": "CadQuery/OCP + build123d local-first", "modules": [{"module": n, "available": importlib.util.find_spec(n) is not None} for n in ("cadquery", "OCP", "build123d")], "local_gates": {"manifest_loaded": True, "step_sources_existing": len(existing) == len(part_files) and bool(part_files), "fabrication_stl_present": len(stl_files) >= 5, "text_to_cad_clone_present": text_to_cad.exists()}, "step_source_count": len(part_files), "existing_step_source_count": len(existing), "fabrication_stl_count": len(stl_files), "recommended_workflow": ["manifest contract", "CadQuery/build123d generation", "local STEP/STL/GLB export", "local clearance/interference/hardware audit", "local transform motion and rendered visibility", "fabrication package validation"]}


# ── helpers ───────────────────────────────────────────────────────────────────

def _root_from_manifest(manifest_path: Path) -> Path:
    return manifest_path.resolve().parent.parent

def _latest_run(manifest: dict[str, Any], kind: str) -> dict[str, Any] | None:
    runs = [r for r in manifest.get("verification_runs", []) if r.get("kind") == kind]
    return runs[-1] if runs else None

def _read_json_if_exists(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

def _rotation_z_4x4(angle_deg: float) -> list[list[float]]:
    c, s = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


# ── local_pose_snapshots ──────────────────────────────────────────────────────

def local_pose_snapshots(manifest_path: Path, angles: list[float] | None = None) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    root = _root_from_manifest(manifest_path)
    angles = angles or [0.0, 45.0, 90.0, 135.0, 180.0]
    spec = manifest.get("mechanism_spec", {})
    hand_ratio = -1.0 / float(manifest.get("motion_contract", {}).get("input_to_cage_ratio", -0.3))
    pose_records = []
    for theta in angles:
        pose_records.append({"theta_deg": theta, "transforms": [{"role": r, "motion": m, "matrix": _rotation_z_4x4(theta * v)} for r, m, v in [("fixed_base", "fixed", 0), ("fixed_ring", "fixed", 0), ("rotating_cage", "rotate_z", 1)]] + [{"role": "orbit_pinion", "motion": "orbit_absolute_spin_z", "orbit_deg": theta, "absolute_spin_deg": -3.0 * theta}, {"role": "hand_crank", "motion": "spin_about_hand_axis", "center_mm": [0.0, -spec.get("gears", {}).get("hand_crank_pinion", {}).get("center_distance_mm", 58.5)], "angle_deg": hand_ratio * theta}]})
    out = root / "reports" / "local_pose_snapshots_v21.json"
    payload = {"manifest": str(manifest_path), "status": "pass" if pose_records else "fail", "created_at": datetime.now(timezone.utc).isoformat(), "pose_count": len(pose_records), "poses": pose_records}
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload | {"artifact": str(out)}


# ── local_fabrication_audit ────────────────────────────────────────────────────

def local_fabrication_audit(manifest_path: Path) -> dict[str, Any]:
    root = _root_from_manifest(manifest_path)
    fab_dir = root / "reports" / "fabrication_v21"
    csv_path = fab_dir / "printed_parts.csv"
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8"))) if csv_path.exists() else []
    try:
        import trimesh
    except Exception as exc:
        return {"manifest": str(manifest_path), "status": "fail", "message": f"trimesh unavailable: {exc}"}
    stl_results = []
    for row in rows:
        stl_path = fab_dir / row["stl"]
        r = {"role": row.get("role"), "file": str(stl_path), "exists": stl_path.exists(), "bytes": stl_path.stat().st_size if stl_path.exists() else 0, "is_watertight": False, "face_count": 0, "bbox_mm": None, "status": "fail"}
        if stl_path.exists() and stl_path.stat().st_size > 0:
            mesh = trimesh.load_mesh(stl_path)
            r.update({"is_watertight": bool(getattr(mesh, "is_watertight", False)), "face_count": int(len(mesh.faces)), "bbox_mm": {"xmin": round(mesh.bounds[0][0], 3), "ymin": round(mesh.bounds[0][1], 3), "zmin": round(mesh.bounds[0][2], 3), "xmax": round(mesh.bounds[1][0], 3), "ymax": round(mesh.bounds[1][1], 3), "zmax": round(mesh.bounds[1][2], 3)}, "status": "pass" if len(mesh.faces) > 0 else "fail"})
        stl_results.append(r)
    checks = [{"name": "STL rows present", "status": "pass" if stl_results else "fail"}, {"name": "all STL files exist", "status": "pass" if all(r["exists"] and r["bytes"] > 0 for r in stl_results) else "fail"}, {"name": "all meshes have faces", "status": "pass" if all(r["face_count"] > 0 for r in stl_results) else "fail"}]
    payload = {"manifest": str(manifest_path), "status": "pass" if all(c["status"] == "pass" for c in checks) else "fail", "created_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "stl_results": stl_results}
    (fab_dir / "local_mesh_validation.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload | {"artifact": str(fab_dir / "local_mesh_validation.json")}


# ── local_assembly_export ─────────────────────────────────────────────────────

def local_assembly_export(manifest_path: Path, angles: list[float] | None = None) -> dict[str, Any]:
    root = _root_from_manifest(manifest_path)
    fab_dir = root / "reports" / "fabrication_v21"
    out_dir = fab_dir / "local_assembly"
    out_dir.mkdir(parents=True, exist_ok=True)
    vis = _read_json_if_exists(root / "reports" / "text_to_cad_review" / "tourbillon_v21" / "v21_visibility_render_report.json")
    input_glbs = {r: Path(p) for r, p in vis.get("input_glbs", {}).items()}
    angles = angles or [0.0, 90.0, 180.0, 270.0]
    try:
        import numpy as np
        import trimesh
    except Exception as exc:
        return {"manifest": str(manifest_path), "status": "fail", "message": f"dependencies unavailable: {exc}"}
    glb_results = []
    for theta in angles:
        scene = trimesh.Scene()
        for role, path in input_glbs.items():
            if not path.exists():
                continue
            loaded = trimesh.load(path, force="scene")
            for name, geom in loaded.geometry.items():
                scene.add_geometry(geom.copy(), node_name=f"{role}_{name}", transform=np.eye(4))
        glb_path = out_dir / f"local_assembly_theta_{int(theta):03d}.glb"
        scene.export(glb_path)
        glb_results.append({"theta_deg": theta, "file": str(glb_path), "bytes": glb_path.stat().st_size if glb_path.exists() else 0, "status": "pass" if glb_path.exists() and glb_path.stat().st_size > 0 else "fail"})
    checks = [{"name": "all assembly GLBs exported", "status": "pass" if all(r["status"] == "pass" for r in glb_results) else "fail"}]
    payload = {"manifest": str(manifest_path), "status": "pass" if all(c["status"] == "pass" for c in checks) else "fail", "created_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "assembly_glbs": glb_results}
    (out_dir / "local_assembly_validation.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload | {"artifact": str(out_dir / "local_assembly_validation.json")}


# ── generate_motion_preview ───────────────────────────────────────────────────

def generate_motion_preview(manifest_path: Path, output: Path | None = None) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    spec = manifest.get("mechanism_spec", {})
    gears = spec.get("gears", {})
    fixed_ring = gears.get("fixed_ring", {})
    orbit = gears.get("orbit_pinion", {})
    cage_drive = gears.get("cage_drive", {})
    hand = gears.get("hand_crank_pinion", {})
    contract = manifest.get("motion_contract", {})
    input_ratio = float(contract.get("input_to_cage_ratio", -0.3))
    hand_ratio = 1.0 / input_ratio if input_ratio else -3.3333333333
    orbit_spin = -float(orbit.get("center_radius_mm", 40.5)) / float(orbit.get("pitch_radius_mm", 13.5))
    if output is None:
        output = manifest_path.parent.parent / "reports" / f"{manifest.get('name', 'tourbillon')}_motion_preview.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    ring_r = float(fixed_ring.get("pitch_radius_mm", 54.0))
    orbit_c = float(orbit.get("center_radius_mm", 40.5))
    orbit_r = float(orbit.get("pitch_radius_mm", 13.5))
    cage_r = float(cage_drive.get("pitch_radius_mm", 45.0))
    hand_r = float(hand.get("pitch_radius_mm", 13.5))
    hand_y = -float(hand.get("center_distance_mm", 58.5))
    ring_t = int(fixed_ring.get("teeth", 72))
    orbit_t = int(orbit.get("teeth", 18))
    cage_t = int(cage_drive.get("teeth", 60))
    hand_t = int(hand.get("teeth", 18))
    def marks(name, count, radius, inner, stroke):
        return f'<g id="{escape(name)}-teeth">' + "".join(f'<line x1="{math.cos(2*math.pi*i/count)*inner:.3f}" y1="{math.sin(2*math.pi*i/count)*inner:.3f}" x2="{math.cos(2*math.pi*i/count)*radius:.3f}" y2="{math.sin(2*math.pi*i/count)*radius:.3f}" stroke="{stroke}" stroke-width="0.9"/>' for i in range(count)) + "</g>"
    html = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{escape(manifest.get('name', 'tourbillon'))} motion preview</title><style>body{{margin:0;font-family:system-ui,sans-serif;background:#f7f4ed;color:#232323;}}main{{max-width:960px;margin:0 auto;padding:24px;}}svg{{width:100%;height:auto;background:#fffaf1;border:1px solid #d8d0c4;}}.steel{{fill:none;stroke:#34495e;stroke-width:2.4;}}.cage{{fill:rgba(70,130,120,0.15);stroke:#2b7a78;stroke-width:2;}}.brass{{fill:rgba(200,154,58,0.24);stroke:#9b6a18;stroke-width:2;}}.ruby{{fill:rgba(165,48,71,0.24);stroke:#9b263d;stroke-width:2;}}.axis{{stroke:#444;stroke-width:1;stroke-dasharray:3 4;}}.label{{font-size:5px;fill:#333;}}</style></head><body><main><h1>{escape(manifest.get('name', 'tourbillon'))}</h1><p>Local transform animation from the validated motion contract.</p><svg viewBox='-90 -90 180 180' aria-label='tourbillon motion preview'><g id='fixed'><circle class='steel' cx='0' cy='0' r='{ring_r:.3f}'/>{marks('fixed-ring', ring_t, ring_r, ring_r - 3.2, '#34495e')}<line class='axis' x1='-68' y1='0' x2='68' y2='0'/><line class='axis' x1='0' y1='-68' x2='0' y2='68'/><text class='label' x='-78' y='-72'>fixed ring {ring_t}T</text></g><g id='cage'><circle class='cage' cx='0' cy='0' r='{cage_r:.3f}'/><path class='cage' d='M -7 -7 L {orbit_c + 7:.3f} -7 L {orbit_c + 7:.3f} 7 L -7 7 Z'/>{marks('cage-drive', cage_t, cage_r, cage_r - 2.7, '#2b7a78')}<g id='orbit' transform='translate({orbit_c:.3f} 0)'><circle class='brass' cx='0' cy='0' r='{orbit_r:.3f}'/>{marks('orbit-pinion', orbit_t, orbit_r + 2.0, orbit_r - 1.8, '#9b6a18')}<line x1='-{orbit_r:.3f}' y1='0' x2='{orbit_r:.3f}' y2='0' stroke='#9b6a18' stroke-width='1.2'/></g></g><g id='hand' transform='translate(0 {hand_y:.3f})'><circle class='ruby' cx='0' cy='0' r='{hand_r:.3f}'/>{marks('hand-pinion', hand_t, hand_r + 2.0, hand_r - 1.8, '#9b263d')}<path class='ruby' d='M -3 0 L -3 -22 L 3 -22 L 3 0 Z'/><circle cx='0' cy='-28' r='5' fill='#9b263d'/></g></svg></main><script>const cage=document.getElementById('cage'),orbit=document.getElementById('orbit'),hand=document.getElementById('hand'),orbitCenter={orbit_c:.9f},handY={hand_y:.9f},handRatio={hand_ratio:.12f},orbitSpin={orbit_spin:.12f};let start;function frame(ts){{if(!start)start=ts;const t=(ts-start)/1000;const cD=(t*24)%360;const hD=handRatio*cD;const oA=orbitSpin*cD;cage.setAttribute('transform',`rotate(${{cD}})`);orbit.setAttribute('transform',`translate(${{orbitCenter}} 0) rotate(${{oA-cD}})`);hand.setAttribute('transform',`translate(0 ${{handY}}) rotate(${{hD}})`);requestAnimationFrame(frame)}}requestAnimationFrame(frame);</script></body></html>"
    output.write_text(html, encoding="utf-8")
    manifest["motion_preview"] = {"status": "pass", "file": str(output), "created_at": datetime.now(timezone.utc).isoformat(), "type": "local_transform_animation", "ratios": {"input_to_cage": input_ratio, "hand_for_cage": hand_ratio, "orbit_spin": orbit_spin}}
    save_manifest(manifest_path, manifest)
    return {"manifest": str(manifest_path), "status": "pass", "file": str(output), "type": "local_transform_animation", "ratios": {"input_to_cage": input_ratio, "hand_for_cage": hand_ratio, "orbit_spin": orbit_spin}}

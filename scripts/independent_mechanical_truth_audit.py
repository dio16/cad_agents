from __future__ import annotations

import json
import math
import os
import platform
import re
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v26_mechanical_package.json"
PACKAGE = ROOT / "reports" / "fabrication_v26_mechanical_package"
STL_DIR = PACKAGE / "stl"
OUT = PACKAGE / "v26_independent_mechanical_truth_audit.json"

POINT_RE = re.compile(r"^\s*vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$")

PART_ROLES = {
    "01_base_plinth_bearing_pocket_v26.stl": {"role": "base", "frame": "world", "expected_single_print_body": True},
    "02_fixed_internal_ring_72t_v26.stl": {"role": "fixed_internal_ring", "frame": "world", "expected_single_print_body": True},
    "03_rotating_carrier_drive_gear_v26.stl": {"role": "carrier", "frame": "world", "expected_single_print_body": True},
    "04_orbit_escape_pinion_18t_v26.stl": {"role": "orbit_escape_pinion", "frame": "local", "axis": [40.5, 0.0], "expected_single_print_body": True},
    "05_hand_crank_pinion_v26.stl": {"role": "hand_crank", "frame": "world_recenter", "axis": [0.0, -58.5], "expected_single_print_body": True},
    "06_balance_wheel_v26.stl": {"role": "balance_wheel", "frame": "local", "axis": [-18.0, 10.0], "expected_single_print_body": True},
    "07_escape_wheel_15t_v26.stl": {"role": "escape_wheel", "frame": "local", "axis": [40.5, 0.0], "expected_single_print_body": True},
    "08_pallet_fork_bridge_v26.stl": {"role": "pallet_fork", "frame": "local", "axis": [10.0, -12.0], "expected_single_print_body": True},
    "09_crank_knob_v26.stl": {"role": "crank_knob", "frame": "local", "axis": [0.0, -58.5], "expected_single_print_body": True},
}

SUPPORT_AXES = {
    "orbit_escape_axis": {"axis": [40.5, 0.0], "moving_role": "orbit_escape_pinion", "role_files": ["04_orbit_escape_pinion_18t_v26.stl", "07_escape_wheel_15t_v26.stl"], "support_file": "03_rotating_carrier_drive_gear_v26.stl", "radius_max": 5.0},
    "balance_axis": {"axis": [-18.0, 10.0], "role_files": ["06_balance_wheel_v26.stl"], "support_file": "03_rotating_carrier_drive_gear_v26.stl", "radius_max": 4.0},
    "pallet_axis": {"axis": [10.0, -12.0], "role_files": ["08_pallet_fork_bridge_v26.stl"], "support_file": "03_rotating_carrier_drive_gear_v26.stl", "radius_max": 4.0},
    "hand_axis": {"axis": [0.0, -58.5], "role_files": ["05_hand_crank_pinion_v26.stl", "09_crank_knob_v26.stl"], "support_file": "01_base_plinth_bearing_pocket_v26.stl", "radius_max": 6.0},
}

EXPECTED_MESH_Z = {
    "hand_pinion_to_carrier_drive_gear": {
        "driver": "05_hand_crank_pinion_v26.stl",
        "driven": "03_rotating_carrier_drive_gear_v26.stl",
        "minimum_face_overlap_mm": 4.0,
    },
    "fixed_internal_ring_to_orbit_escape_pinion": {
        "driver": "02_fixed_internal_ring_72t_v26.stl",
        "driven": "04_orbit_escape_pinion_18t_v26.stl",
        "minimum_face_overlap_mm": 4.0,
    },
}


def is_wsl() -> bool:
    try:
        version = Path("/proc/version").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        version = ""
    return "microsoft" in version or "wsl" in version


def parse_ascii_stl(path: Path) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    vertices: list[tuple[float, float, float]] = []
    triangles = []
    for line in path.read_text(encoding="ascii", errors="strict").splitlines():
        match = POINT_RE.match(line)
        if not match:
            continue
        vertices.append(tuple(float(match.group(i)) for i in range(1, 4)))
        if len(vertices) == 3:
            triangles.append((vertices[0], vertices[1], vertices[2]))
            vertices = []
    if vertices:
        raise ValueError(f"dangling STL vertices in {path}")
    return triangles


def qvertex(vertex: tuple[float, float, float], scale: float = 1000.0) -> tuple[int, int, int]:
    return tuple(int(round(v * scale)) for v in vertex)


def tri_area(tri: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]) -> float:
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    return 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)


def mesh_stats(path: Path) -> dict:
    triangles = parse_ascii_stl(path)
    points = [p for tri in triangles for p in tri]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    qtris = [tuple(qvertex(p) for p in tri) for tri in triangles]
    edge_counts: Counter[tuple[tuple[int, int, int], tuple[int, int, int]]] = Counter()
    vertex_to_tris: defaultdict[tuple[int, int, int], list[int]] = defaultdict(list)
    for idx, tri in enumerate(qtris):
        for vertex in tri:
            vertex_to_tris[vertex].append(idx)
        for i, j in [(0, 1), (1, 2), (2, 0)]:
            a, b = tri[i], tri[j]
            edge_counts[tuple(sorted((a, b)))] += 1
    adjacency = [set() for _ in triangles]
    for owners in vertex_to_tris.values():
        if len(owners) <= 1:
            continue
        for owner in owners:
            adjacency[owner].update(o for o in owners if o != owner)
    seen = [False] * len(triangles)
    components = []
    for start in range(len(triangles)):
        if seen[start]:
            continue
        queue: deque[int] = deque([start])
        seen[start] = True
        count = 0
        while queue:
            current = queue.popleft()
            count += 1
            for nxt in adjacency[current]:
                if not seen[nxt]:
                    seen[nxt] = True
                    queue.append(nxt)
        components.append(count)
    return {
        "file": path.name,
        "triangle_count": len(triangles),
        "bbox_mm": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]},
        "degenerate_triangles": sum(1 for tri in triangles if tri_area(tri) <= 1e-8),
        "unique_vertices": len(vertex_to_tris),
        "connected_triangle_components": len(components),
        "largest_component_triangles": max(components) if components else 0,
        "boundary_edges": sum(1 for count in edge_counts.values() if count == 1),
        "nonmanifold_edges": sum(1 for count in edge_counts.values() if count > 2),
        "triangles": triangles,
        "vertices": points,
    }


def bbox_overlap(a: dict, b: dict) -> tuple[float, float, float]:
    overlaps = []
    for axis in "xyz":
        lo = max(a[axis][0], b[axis][0])
        hi = min(a[axis][1], b[axis][1])
        overlaps.append(max(0.0, hi - lo))
    return tuple(overlaps)


def z_overlap(stats: dict, a: str, b: str) -> float:
    return bbox_overlap(stats[a]["bbox_mm"], stats[b]["bbox_mm"])[2]


def support_vertex_count(stats: dict, support_file: str, axis: list[float], z_min: float, z_max: float, radius_max: float) -> int:
    ax, ay = axis
    count = 0
    for x, y, z in stats[support_file]["vertices"]:
        if z < z_min or z > z_max:
            continue
        if math.hypot(x - ax, y - ay) <= radius_max:
            count += 1
    return count


def add_check(checks: list[dict], name: str, passed: bool, severity: str = "P1", **detail: object) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "severity": severity, **detail})


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    checks: list[dict] = []
    add_check(checks, "audit is running inside WSL", is_wsl(), "P0", platform=platform.platform(), cwd=str(Path.cwd()))
    add_check(checks, "audit is independent from legacy package validation JSON", True, "P0", legacy_validation_used=False)

    expected_files = set(manifest["printable_parts"])
    role_files = set(PART_ROLES)
    add_check(checks, "manifest printable parts match independent role map", expected_files == role_files, "P0", manifest_count=len(expected_files), role_map_count=len(role_files), missing=sorted(expected_files - role_files), extra=sorted(role_files - expected_files))

    stats: dict[str, dict] = {}
    for filename in sorted(role_files):
        path = STL_DIR / filename
        add_check(checks, f"{filename} exists in WSL package", path.exists() and path.stat().st_size > 1000, "P0", path=str(path), bytes=path.stat().st_size if path.exists() else 0)
        if path.exists():
            stats[filename] = mesh_stats(path)
            add_check(checks, f"{filename} has finite nondegenerate mesh", stats[filename]["triangle_count"] > 20 and stats[filename]["degenerate_triangles"] == 0, "P0", triangles=stats[filename]["triangle_count"], degenerate_triangles=stats[filename]["degenerate_triangles"])
            add_check(checks, f"{filename} is manifold enough for a printable solid", stats[filename]["boundary_edges"] == 0 and stats[filename]["nonmanifold_edges"] == 0, "P0", boundary_edges=stats[filename]["boundary_edges"], nonmanifold_edges=stats[filename]["nonmanifold_edges"])
            single_body_ok = stats[filename]["connected_triangle_components"] == 1
            add_check(checks, f"{filename} is one connected printable body", single_body_ok, "P0", connected_triangle_components=stats[filename]["connected_triangle_components"], largest_component_triangles=stats[filename]["largest_component_triangles"])

    if set(stats) == role_files:
        for mesh_name, pair in EXPECTED_MESH_Z.items():
            overlap = z_overlap(stats, pair["driver"], pair["driven"])
            add_check(checks, f"{mesh_name} has real axial face overlap", overlap >= pair["minimum_face_overlap_mm"], "P0", overlap_mm=round(overlap, 3), minimum_mm=pair["minimum_face_overlap_mm"])

        for name, axis_spec in SUPPORT_AXES.items():
            role_z0 = min(stats[file]["bbox_mm"]["z"][0] for file in axis_spec["role_files"])
            role_z1 = max(stats[file]["bbox_mm"]["z"][1] for file in axis_spec["role_files"])
            lower_count = support_vertex_count(stats, axis_spec["support_file"], axis_spec["axis"], role_z0 - 8.0, role_z0 + 0.05, axis_spec["radius_max"])
            upper_count = support_vertex_count(stats, axis_spec["support_file"], axis_spec["axis"], role_z1 - 0.05, role_z1 + 8.0, axis_spec["radius_max"])
            add_check(checks, f"{name} has lower and upper local support material", lower_count > 12 and upper_count > 12, "P0", role_z_mm=[round(role_z0, 3), round(role_z1, 3)], lower_support_vertices=lower_count, upper_support_vertices=upper_count, support_file=axis_spec["support_file"])

        # Coarse static overlap rejects obvious non-gear, non-fastener body intersections before any visual claim.
        allowed_static_pairs = {
            tuple(sorted(pair))
            for pair in [
                ("02_fixed_internal_ring_72t_v26.stl", "04_orbit_escape_pinion_18t_v26.stl"),
                ("03_rotating_carrier_drive_gear_v26.stl", "05_hand_crank_pinion_v26.stl"),
            ]
        }
        overlap_pairs = []
        files = sorted(stats)
        for i, a in enumerate(files):
            for b in files[i + 1 :]:
                overlap = bbox_overlap(stats[a]["bbox_mm"], stats[b]["bbox_mm"])
                if min(overlap) > 0 and tuple(sorted((a, b))) not in allowed_static_pairs:
                    overlap_pairs.append({"a": a, "b": b, "overlap_mm": [round(v, 3) for v in overlap]})
        add_check(checks, "coarse static bbox interference has only declared gear mesh overlaps", not overlap_pairs, "P0", overlap_pairs=overlap_pairs[:20], overlap_pair_count=len(overlap_pairs))

    motion_path = PACKAGE / "v26_motion_validation.json"
    motion = json.loads(motion_path.read_text(encoding="utf-8")) if motion_path.exists() else {}
    joints = {joint.get("role"): joint for joint in motion.get("joints", [])}
    add_check(checks, "motion report declares carrier, hand, orbit, escape, balance, and pallet joints", {"carrier", "hand_crank", "orbit_escape_pinion", "escape_wheel", "balance", "pallet"}.issubset(joints), "P0", roles=sorted(joints))
    add_check(checks, "escape wheel is parented to orbit shaft in motion contract", joints.get("escape_wheel", {}).get("parent") == "orbit_escape_pinion", "P0", escape_joint=joints.get("escape_wheel"))
    add_check(checks, "visible escapement is not falsely claimed as mechanically regulating", manifest.get("escapement_demonstrator", {}).get("limitation", "").startswith("visual and kinematic"), "P1", limitation=manifest.get("escapement_demonstrator", {}).get("limitation"))
    add_check(checks, "mechanical drive path from escape wheel to pallet and balance is physically modeled", False, "P0", reason="Current V26 uses visual_oscillation for balance and pallet; no contact/impulse/locking geometry or gear/jewel interaction is validated.")

    html_path = PACKAGE / "v26_3d_cad_motion_viewer.html"
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    viewer_tokens = ["poseSlider", "explodeSlider", "sectionSlider", "toggleSupports", "ratioContract", "orbitGroup.add(escGroup)", "requestAnimationFrame"]
    add_check(checks, "viewer contains required inspection controls", all(token in html for token in viewer_tokens), "P1", missing=[token for token in viewer_tokens if token not in html])
    smoke_path = PACKAGE / "wsl_http_viewer_smoke.json"
    smoke = json.loads(smoke_path.read_text(encoding="utf-8")) if smoke_path.exists() else {"status": "missing"}
    add_check(checks, "viewer is served-testable over WSL HTTP instead of file URL", smoke.get("status") == "pass", "P1", smoke_file=str(smoke_path), smoke_status=smoke.get("status"))

    fail_count = sum(1 for check in checks if check["status"] != "pass")
    p0_fail_count = sum(1 for check in checks if check["status"] != "pass" and check["severity"] == "P0")
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if fail_count == 0 else "fail",
        "completion_allowed": fail_count == 0,
        "p0_fail_count": p0_fail_count,
        "fail_count": fail_count,
        "checks": checks,
        "part_mesh_stats": {
            name: {k: v for k, v in item.items() if k not in {"triangles", "vertices"}}
            for name, item in stats.items()
        },
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "fail_count": fail_count, "p0_fail_count": p0_fail_count, "report": str(OUT)}, indent=2))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

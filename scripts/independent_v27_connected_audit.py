from __future__ import annotations

import json
import math
import platform
import re
import struct
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from v27_evidence import evidence_fields


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v27_connected_contract.json"
PACKAGE = ROOT / "reports" / "fabrication_v27_connected_package"
OUT = PACKAGE / "v27_independent_connected_audit.json"
POINT_RE = re.compile(r"^\s*vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$")


def is_wsl() -> bool:
    try:
        version = Path("/proc/version").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        version = ""
    return platform.system() == "Linux" and ("microsoft" in version or "wsl" in version)


def qvertex(vertex: tuple[float, float, float], scale: float = 1000.0) -> tuple[int, int, int]:
    return tuple(int(round(v * scale)) for v in vertex)


def parse_ascii_stl(path: Path) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    data = path.read_bytes()
    if len(data) >= 84:
        count = struct.unpack("<I", data[80:84])[0]
        expected = 84 + count * 50
        if expected == len(data):
            triangles = []
            offset = 84
            for _ in range(count):
                values = struct.unpack("<12fH", data[offset : offset + 50])
                triangles.append((values[3:6], values[6:9], values[9:12]))
                offset += 50
            return triangles
    vertices: list[tuple[float, float, float]] = []
    triangles = []
    for line in data.decode("ascii", errors="strict").splitlines():
        match = POINT_RE.match(line)
        if not match:
            continue
        vertices.append(tuple(float(match.group(i)) for i in range(1, 4)))
        if len(vertices) == 3:
            triangles.append((vertices[0], vertices[1], vertices[2]))
            vertices = []
    return triangles


def stl_components(path: Path) -> dict:
    triangles = parse_ascii_stl(path)
    points = [p for tri in triangles for p in tri]
    vertex_to_tris: defaultdict[tuple[int, int, int], list[int]] = defaultdict(list)
    edge_counts: Counter[tuple[tuple[int, int, int], tuple[int, int, int]]] = Counter()
    for idx, tri in enumerate(triangles):
        qtri = [qvertex(p) for p in tri]
        for vertex in qtri:
            vertex_to_tris[vertex].append(idx)
        for i, j in [(0, 1), (1, 2), (2, 0)]:
            edge_counts[tuple(sorted((qtri[i], qtri[j])))] += 1
    adjacency = [set() for _ in triangles]
    for owners in vertex_to_tris.values():
        for owner in owners:
            adjacency[owner].update(o for o in owners if o != owner)
    seen = [False] * len(triangles)
    component_summaries = []
    for start in range(len(triangles)):
        if seen[start]:
            continue
        queue = deque([start])
        seen[start] = True
        component = []
        while queue:
            cur = queue.popleft()
            component.append(cur)
            for nxt in adjacency[cur]:
                if not seen[nxt]:
                    seen[nxt] = True
                    queue.append(nxt)
        component_points = [point for tri_idx in component for point in triangles[tri_idx]]
        cxs = [p[0] for p in component_points]
        cys = [p[1] for p in component_points]
        czs = [p[2] for p in component_points]
        component_summaries.append(
            {
                "triangle_count": len(component),
                "bbox_mm": {
                    "x": [min(cxs), max(cxs)],
                    "y": [min(cys), max(cys)],
                    "z": [min(czs), max(czs)],
                },
            }
        )
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return {
        "triangle_count": len(triangles),
        "connected_triangle_components": len(component_summaries),
        "component_summaries": sorted(component_summaries, key=lambda item: item["triangle_count"], reverse=True),
        "boundary_edges": sum(1 for count in edge_counts.values() if count == 1),
        "nonmanifold_edges": sum(1 for count in edge_counts.values() if count > 2),
        "bbox_mm": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]},
    }


def add(checks: list[dict], name: str, passed: bool, severity: str = "P1", **detail: object) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "severity": severity, **detail})


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    checks: list[dict] = []
    add(checks, "audit is running inside WSL", is_wsl(), "P0")
    add(checks, "V27 manifest remains non-completion candidate", manifest.get("completion_allowed") is False, "P0", manifest_status=manifest.get("status"))
    stats = {}
    for item in manifest["parts"]:
        step = Path(item["step"])
        stl = Path(item["stl"])
        if not step.is_absolute():
            step = ROOT / step
        if not stl.is_absolute():
            stl = ROOT / stl
        add(checks, f"{item['name']} STEP exists", step.exists() and step.stat().st_size > 1000, "P0", path=str(step), bytes=step.stat().st_size if step.exists() else 0)
        add(checks, f"{item['name']} STL exists", stl.exists() and stl.stat().st_size > 1000, "P0", path=str(stl), bytes=stl.stat().st_size if stl.exists() else 0)
        if step.exists():
            shape = cq.importers.importStep(str(step))
            solid_count = len(shape.val().Solids())
            add(checks, f"{item['name']} imports as one OCP solid", solid_count == 1, "P0", solid_count=solid_count)
        if stl.exists():
            s = stl_components(stl)
            stats[item["name"]] = s
            add(checks, f"{item['name']} STL has one connected triangle component", s["connected_triangle_components"] == 1, "P0", connected_triangle_components=s["connected_triangle_components"])
            add(checks, f"{item['name']} STL has no open or nonmanifold edges", s["boundary_edges"] == 0 and s["nonmanifold_edges"] == 0, "P0", boundary_edges=s["boundary_edges"], nonmanifold_edges=s["nonmanifold_edges"])
    carrier = stats.get("03_rotating_carrier_drive_gear_v27")
    if carrier:
        add(checks, "carrier clears tabletop plane", carrier["bbox_mm"]["z"][0] >= 0.0, "P0", carrier_z=carrier["bbox_mm"]["z"])
    drive_model = manifest.get("escapement_drive_model", {})
    pin_radius = drive_model.get("escape_pin_radius_mm", 0.0)
    pin_offset = drive_model.get("escape_pin_offset_mm", 0.0)
    slot_width = drive_model.get("slot_width_mm", 0.0)
    slot_span = drive_model.get("slot_centerline_span_mm", [0.0, 0.0])
    add(
        checks,
        "escapement has explicit physical drive model or remains blocked",
        drive_model.get("type") == "eccentric_pin_slot_pallet_display"
        and pin_radius > 0
        and pin_offset > 0
        and slot_width > 0
        and len(slot_span) == 2
        and slot_span[1] > slot_span[0],
        "P0",
        drive_model=drive_model,
    )
    add(
        checks,
        "escapement drive claim is limited to tabletop display mechanism",
        "watch-grade escapement" in drive_model.get("blocked_claims", [])
        and "regulating balance" in drive_model.get("blocked_claims", []),
        "P0",
        blocked_claims=drive_model.get("blocked_claims", []),
    )
    fail_count = sum(c["status"] != "pass" for c in checks)
    p0_fail_count = sum(c["status"] != "pass" and c["severity"] == "P0" for c in checks)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        **evidence_fields(),
        "status": "pass" if fail_count == 0 else "fail",
        "completion_allowed": False,
        "fail_count": fail_count,
        "p0_fail_count": p0_fail_count,
        "checks": checks,
        "part_mesh_stats": stats,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "fail_count": fail_count, "p0_fail_count": p0_fail_count, "report": str(OUT)}, indent=2))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

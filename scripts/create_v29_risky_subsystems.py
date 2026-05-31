from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from cadquery import exporters
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "fabrication_v29_risky_subsystems"
STEP = OUT / "step"
STL = OUT / "stl"
SHEET = OUT / "v29_risky_subsystems_contact_sheet.png"


def cyl_z(radius: float, height: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((x, y, z))


def cyl_x(radius: float, length: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("YZ").circle(radius).extrude(length).translate((x, y, z))


def box(x: float, y: float, z: float, cx: float = 0.0, cy: float = 0.0, cz: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate((cx, cy, cz))


def export(name: str, shape: cq.Workplane) -> dict:
    STEP.mkdir(parents=True, exist_ok=True)
    STL.mkdir(parents=True, exist_ok=True)
    step = STEP / f"{name}.step"
    stl = STL / f"{name}.stl"
    exporters.export(shape, str(step))
    exporters.export(shape, str(stl), tolerance=0.12, angularTolerance=0.12)
    bb = shape.val().BoundingBox()
    return {
        "name": name,
        "step": str(step),
        "stl": str(stl),
        "bbox_mm": {
            "x": [round(bb.xmin, 2), round(bb.xmax, 2)],
            "y": [round(bb.ymin, 2), round(bb.ymax, 2)],
            "z": [round(bb.zmin, 2), round(bb.zmax, 2)],
        },
    }


def rotate_xyz(point: tuple[float, float, float], yaw_deg: float, pitch_deg: float) -> tuple[float, float, float]:
    x, y, z = point
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    x1 = x * math.cos(yaw) - y * math.sin(yaw)
    y1 = x * math.sin(yaw) + y * math.cos(yaw)
    z1 = z
    y2 = y1 * math.cos(pitch) - z1 * math.sin(pitch)
    z2 = y1 * math.sin(pitch) + z1 * math.cos(pitch)
    return x1, y2, z2


def render_panel(
    shape: cq.Workplane,
    label: str,
    color: tuple[int, int, int],
    yaw_deg: float,
    pitch_deg: float,
    width: int = 420,
    height: int = 320,
) -> Image.Image:
    verts, faces = shape.val().tessellate(0.8, 0.25)
    rotated = [rotate_xyz((v.x, v.y, v.z), yaw_deg, pitch_deg) for v in verts]
    xs = [p[0] for p in rotated]
    ys = [p[1] for p in rotated]
    span_x = max(xs) - min(xs) or 1.0
    span_y = max(ys) - min(ys) or 1.0
    scale = min((width - 36) / span_x, (height - 54) / span_y)
    x_mid = (max(xs) + min(xs)) / 2.0
    y_mid = (max(ys) + min(ys)) / 2.0

    def project(index: int) -> tuple[int, int]:
        x, y, _ = rotated[index]
        return (
            round(width / 2 + (x - x_mid) * scale),
            round(height / 2 - 4 - (y - y_mid) * scale),
        )

    panel = Image.new("RGB", (width, height), (18, 24, 32))
    draw = ImageDraw.Draw(panel)
    triangles = []
    for face in faces:
        z_avg = sum(rotated[index][2] for index in face) / 3.0
        triangles.append((z_avg, [project(index) for index in face]))
    for _, points in sorted(triangles):
        draw.polygon(points, fill=color)
    draw.rectangle((0, 0, width, 30), fill=(18, 24, 32))
    draw.text((12, 9), label, fill=(238, 243, 246))
    return panel


def write_contact_sheet(parts: dict[str, cq.Workplane]) -> None:
    panels = [
        render_panel(
            parts["01_autonomous_power_module_concept"],
            "01 autonomous power module",
            (210, 153, 58),
            32,
            18,
        ),
        render_panel(
            parts["02_spatial_riser_concept"],
            "02 spatial riser",
            (88, 145, 181),
            35,
            18,
        ),
        render_panel(
            parts["03_canted_cage_sightline_concept"],
            "03 canted cage sightline",
            (211, 88, 133),
            25,
            22,
        ),
    ]
    sheet = Image.new("RGB", (420 * 3, 320), (18, 24, 32))
    for index, panel in enumerate(panels):
        sheet.paste(panel, (index * 420, 0))
    sheet.save(SHEET)


def power_module() -> cq.Workplane:
    return (
        box(110, 36, 8, 0, 0, 4)
        .union(box(25, 40, 20, -35, 0, 18))
        .union(cyl_x(40, 8, 15, 0, 36))
        .union(cyl_x(18, 24, -6, 0, 20))
        .union(cyl_x(3, 76, -18, 0, 20))
        .clean()
    )


def spatial_riser() -> cq.Workplane:
    horizontal = cyl_x(3, 70, -35, 0, 20)
    lower_hub = cyl_z(10, 8, 0, 0, 16)
    upper_hub = cyl_z(10, 8, 0, 0, 58)
    vertical = cyl_z(3, 34, 0, 0, 24)
    bridge = box(24, 24, 8, 0, 0, 62)
    return horizontal.union(lower_hub).union(upper_hub).union(vertical).union(bridge).clean()


def canted_cage_sightline() -> cq.Workplane:
    outer = cq.Workplane("XY").circle(45).circle(36).extrude(5)
    spokes = cq.Workplane("XY").box(78, 5, 5).union(cq.Workplane("XY").box(5, 78, 5))
    fine_zone = cyl_z(10, 4, -12, 10, 7).union(cyl_z(6, 4, 16, 0, 7)).union(cyl_z(14, 3, -24, 12, 7))
    cage = outer.union(spokes).union(fine_zone).translate((0, 0, 24))
    return cage.rotate((0, 0, 24), (1, 0, 24), 30).clean()


def main() -> int:
    parts = {
        "01_autonomous_power_module_concept": power_module(),
        "02_spatial_riser_concept": spatial_riser(),
        "03_canted_cage_sightline_concept": canted_cage_sightline(),
    }
    stats = [export(name, shape) for name, shape in parts.items()]
    write_contact_sheet(parts)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "claim": "concept geometry only; not fabrication complete",
        "source_contract": "manifests/tourbillon_v29_risky_subsystems_contract.json",
        "contact_sheet": str(SHEET),
        "parameters": {
            "canted_cage_tilt_deg": 30,
            "spatial_riser_axis_lift_mm": 42,
            "visible_winding_drum_nominal_diameter_mm": 80,
        },
        "module_roles": {
            "01_autonomous_power_module_concept": [
                "motor_chamber",
                "visible_winding_drum",
                "storage_barrel",
                "output_shaft",
            ],
            "02_spatial_riser_concept": [
                "horizontal_input_shaft",
                "lower_hub",
                "vertical_transfer_shaft",
                "upper_hub",
                "elevated_output",
            ],
            "03_canted_cage_sightline_concept": [
                "open_cage",
                "spokes",
                "fast_fine_zone",
            ],
        },
        "modules": stats,
        "checks": {
            "three_risky_subsystems_present": len(stats) == 3,
            "power_module_has_macro_motion_envelope": stats[0]["bbox_mm"]["z"][1] >= 70,
            "spatial_riser_changes_axis_height": stats[1]["bbox_mm"]["z"][1] >= 60,
            "canted_cage_has_tilted_envelope": stats[2]["bbox_mm"]["z"][1] > stats[2]["bbox_mm"]["z"][0],
            "contact_sheet_exists": SHEET.exists() and SHEET.stat().st_size > 0,
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "v29_risky_subsystems_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

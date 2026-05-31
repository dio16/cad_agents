from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from cadquery import exporters
from PIL import Image

from create_v29_risky_subsystems import cyl_x, cyl_z, render_panel


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "fabrication_v29_architecture_demonstrator"
STEP = OUT / "step"
STL = OUT / "stl"
SHEET = OUT / "v29_architecture_demonstrator_contact_sheet.png"


def architecture_shape() -> cq.Workplane:
    drum = cyl_x(40, 8, -80, 0, 40)
    barrel = cyl_x(18, 18, -44, 0, 20)
    transfer = cyl_x(3, 44, -44, 0, 20)
    lower_hub = cyl_z(10, 8, 0, 0, 16)
    vertical = cyl_z(3, 34, 0, 0, 24)
    upper_hub = cyl_z(10, 8, 0, 0, 58)
    carrier_ring = cq.Workplane("XY").circle(42).circle(34).extrude(5).translate((36, 0, 62))
    spokes = cq.Workplane("XY").box(74, 5, 5).union(cq.Workplane("XY").box(5, 74, 5)).translate((36, 0, 62))
    fine_zone = (
        cyl_z(10, 4, 24, 10, 64)
        .union(cyl_z(6, 4, 52, 0, 64))
        .union(cyl_z(14, 3, 12, 12, 64))
    )
    cage = carrier_ring.union(spokes).union(fine_zone).rotate((36, 0, 62), (37, 0, 62), 30)
    return drum.union(barrel).union(transfer).union(lower_hub).union(vertical).union(upper_hub).union(cage).clean()


def write_contact_sheet(shape: cq.Workplane) -> None:
    panels = [
        render_panel(shape, "front oblique", (210, 153, 58), 30, 18),
        render_panel(shape, "side spatial transition", (88, 145, 181), 90, 10),
        render_panel(shape, "topology overview", (211, 88, 133), 0, 70),
    ]
    sheet = Image.new("RGB", (420 * 3, 320), (18, 24, 32))
    for index, panel in enumerate(panels):
        sheet.paste(panel, (index * 420, 0))
    sheet.save(SHEET)


def main() -> int:
    STEP.mkdir(parents=True, exist_ok=True)
    STL.mkdir(parents=True, exist_ok=True)
    shape = architecture_shape()
    step = STEP / "v29_architecture_demonstrator.step"
    stl = STL / "v29_architecture_demonstrator.stl"
    exporters.export(shape, str(step))
    exporters.export(shape, str(stl), tolerance=0.12, angularTolerance=0.12)
    write_contact_sheet(shape)
    bb = shape.val().BoundingBox()
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "claim": "architecture demonstrator only; not detailed sculpture geometry or fabrication complete",
        "source_contracts": [
            "manifests/tourbillon_v29_full_assembly_contract.json",
            "manifests/tourbillon_v29_kinematic_dimension_contract.json",
        ],
        "artifacts": {
            "step": str(step),
            "stl": str(stl),
            "contact_sheet": str(SHEET),
        },
        "bbox_mm": {
            "x": [round(bb.xmin, 2), round(bb.xmax, 2)],
            "y": [round(bb.ymin, 2), round(bb.ymax, 2)],
            "z": [round(bb.zmin, 2), round(bb.zmax, 2)],
        },
        "represented_motion_classes": [
            "slow_macro",
            "medium_transfer",
            "fast_fine",
        ],
        "represented_spatial_transitions": [
            "low_plane_to_elevated_plane",
            "elevated_plane_to_canted_display",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "v29_architecture_demonstrator_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

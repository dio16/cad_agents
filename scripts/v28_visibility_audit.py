from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

from v28_sampled_motion_audit import placed_shapes

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifests' / 'tourbillon_v28_mechanism_contract.json'
PACKAGE = ROOT / 'reports' / 'fabrication_v28_mechanism_package'
OUT = PACKAGE / 'v28_visibility_audit.json'
SHEET = PACKAGE / 'v28_visibility_contact_sheet.png'
SAMPLES = [0, 90, 180, 270]
CANVAS_PX = 460
WORLD_LIMIT_MM = 76.0
MIN_PROJECTED_PIXELS = 24
ROLE_TO_PART = {
    'carrier': '03_rotating_carrier_drive_gear_v28',
    'orbit_escape_pinion': '04_orbit_escape_pinion_18t_v28',
    'hand_input_pinion': '05_hand_crank_pinion_v28',
    'balance_wheel': '06_balance_wheel_v28',
    'escape_wheel': '07_escape_wheel_15t_v28',
    'pallet_fork': '08_pallet_fork_bridge_v28',
}
ROLE_COLORS = {
    'carrier': (217, 169, 76),
    'orbit_escape_pinion': (232, 121, 45),
    'hand_input_pinion': (204, 72, 126),
    'balance_wheel': (240, 209, 112),
    'escape_wheel': (237, 133, 49),
    'pallet_fork': (232, 224, 211),
}


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def mm_to_px(x_mm: float, y_mm: float) -> tuple[int, int]:
    span = 2.0 * WORLD_LIMIT_MM
    x_px = round((x_mm + WORLD_LIMIT_MM) / span * (CANVAS_PX - 1))
    y_px = round((WORLD_LIMIT_MM - y_mm) / span * (CANVAS_PX - 1))
    return x_px, y_px


def projected_triangles(shape) -> list[list[tuple[int, int]]]:
    vertices, faces = shape.val().tessellate(0.6, 0.2)
    triangles = []
    for face in faces:
        points = [mm_to_px(vertices[index].x, vertices[index].y) for index in face]
        triangles.append(points)
    return triangles


def draw_shape(image: Image.Image, shape, fill: tuple[int, int, int] | int) -> int:
    draw = ImageDraw.Draw(image)
    for triangle in projected_triangles(shape):
        draw.polygon(triangle, fill=fill)
    if image.mode == 'L':
        return sum(1 for pixel in image.getdata() if pixel)
    return 0


def panel_path(theta: int) -> Path:
    return PACKAGE / f'v28_visibility_{theta:03d}.png'


def render_panel(theta: int, shapes: dict[str, object]) -> Path:
    panel = Image.new('RGB', (CANVAS_PX, CANVAS_PX), (18, 24, 32))
    draw = ImageDraw.Draw(panel)
    center = CANVAS_PX // 2
    ring_radius = round(64.0 / (2.0 * WORLD_LIMIT_MM) * CANVAS_PX)
    draw.ellipse(
        (center - ring_radius, center - ring_radius, center + ring_radius, center + ring_radius),
        outline=(79, 120, 151),
        width=4,
    )
    for role in ['carrier', 'hand_input_pinion', 'orbit_escape_pinion', 'balance_wheel', 'escape_wheel', 'pallet_fork']:
        draw_shape(panel, shapes[ROLE_TO_PART[role]], ROLE_COLORS[role])
    draw.rectangle((8, 8, 126, 34), fill=(18, 24, 32))
    draw.text((16, 15), f'carrier {theta} deg', fill=(238, 243, 246))
    path = panel_path(theta)
    panel.save(path)
    return path


def write_contact_sheet(panel_paths: list[tuple[int, Path]]) -> None:
    tile_px = CANVAS_PX
    label_h = 24
    sheet = Image.new('RGB', (tile_px * 2, (tile_px + label_h) * 2), (18, 24, 32))
    draw = ImageDraw.Draw(sheet)
    for index, (theta, path) in enumerate(panel_paths):
        x = (index % 2) * tile_px
        y = (index // 2) * (tile_px + label_h)
        sheet.paste(Image.open(path).convert('RGB'), (x, y + label_h))
        draw.text((x + 12, y + 5), f'V28 local STEP projection / carrier {theta} deg', fill=(238, 243, 246))
    sheet.save(SHEET)


def main() -> int:
    manifest = load_manifest()
    projected_pixels = {role: [] for role in ROLE_TO_PART}
    panels: list[tuple[int, Path]] = []
    for theta in SAMPLES:
        shapes, _, _, _ = placed_shapes(manifest, theta)
        panels.append((theta, render_panel(theta, shapes)))
        for role, part_name in ROLE_TO_PART.items():
            mask = Image.new('L', (CANVAS_PX, CANVAS_PX), 0)
            projected_pixels[role].append(
                {'carrier_deg': theta, 'projected_pixels': draw_shape(mask, shapes[part_name], 255)}
            )
    write_contact_sheet(panels)
    checks = [
        {
            'name': f'{role} remains represented in every sampled local-geometry top view',
            'status': 'pass'
            if min(sample['projected_pixels'] for sample in samples) >= MIN_PROJECTED_PIXELS
            else 'fail',
            'min_projected_pixels': min(sample['projected_pixels'] for sample in samples),
            'samples': samples,
        }
        for role, samples in projected_pixels.items()
    ]
    checks.append(
        {
            'name': 'contact sheet exists and is nonempty',
            'status': 'pass' if SHEET.exists() and SHEET.stat().st_size > 0 else 'fail',
            'path': str(SHEET),
        }
    )
    status = 'pass' if all(check['status'] == 'pass' for check in checks) else 'fail'
    report = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'source_manifest': str(MANIFEST),
        'sample_angles_deg': SAMPLES,
        'visible_moving_roles': list(ROLE_TO_PART),
        'artifact_kind': 'deterministic_top_view_contact_sheet_from_local_step_geometry',
        'detector': {
            'mode': 'per_role_projected_step_silhouette',
            'minimum_projected_pixels': MIN_PROJECTED_PIXELS,
            'occlusion_aware': False,
        },
        'limitation': (
            'This proves sampled local-geometry representation for the named moving roles. '
            'It is not a live viewer, native CAD animation, or occlusion-aware visibility claim.'
        ),
        'contact_sheet': str(SHEET),
        'panels': [{'carrier_deg': theta, 'path': str(path)} for theta, path in panels],
        'checks': checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status': status, 'report': str(OUT), 'contact_sheet': str(SHEET)}, indent=2))
    return 0 if status == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())

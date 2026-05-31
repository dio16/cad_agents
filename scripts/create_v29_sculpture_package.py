from __future__ import annotations

import base64
import csv
import json
import math
import struct
from datetime import datetime, timezone
from pathlib import Path

import cadquery as cq
from cadquery import exporters
from PIL import Image, ImageDraw

from create_v28_mechanism_package import annulus, box, cyl, gear, internal_gear, union_all
from create_v29_risky_subsystems import rotate_xyz
from independent_v27_connected_audit import parse_ascii_stl


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "fabrication_v29_sculpture_package"
STEP = OUT / "step"
STL = OUT / "stl"
VIEWER = OUT / "v29_3d_cad_motion_viewer.html"
SHEET = OUT / "v29_visibility_contact_sheet.png"
SUMMARY = OUT / "v29_package_summary.json"
MANIFEST = ROOT / "manifests" / "tourbillon_v29_sculpture_geometry_contract.json"
GEOMETRY_VALIDATION = ROOT / "reports" / "v29_sculpture_geometry_contract_validation.json"
FEASIBILITY_VALIDATION = ROOT / "reports" / "v29_selected_design_feasibility_validation.json"


def canted(shape: cq.Workplane, center=(45.0, 0.0, 62.0)) -> cq.Workplane:
    return shape.rotate((0, 0, 0), (1, 0, 0), 30).translate(center)


def x_axis_gear(teeth: int, root: float, tip: float, length: float, cx: float, cy: float, cz: float, tooth_width: float = 2.0) -> cq.Workplane:
    return gear(teeth, root, tip, -length / 2, length / 2, tooth_width=tooth_width).rotate((0, 0, 0), (0, 1, 0), 90).translate((cx, cy, cz))


def export(name: str, shape: cq.Workplane) -> dict:
    STEP.mkdir(parents=True, exist_ok=True)
    STL.mkdir(parents=True, exist_ok=True)
    step = STEP / f"{name}.step"
    stl = STL / f"{name}.stl"
    exporters.export(shape, str(step))
    exporters.export(shape, str(stl), tolerance=0.1, angularTolerance=0.1)
    bb = shape.val().BoundingBox()
    return {
        "name": name,
        "step": str(step),
        "stl": str(stl),
        "bbox_mm": {
            "x": [round(bb.xmin, 3), round(bb.xmax, 3)],
            "y": [round(bb.ymin, 3), round(bb.ymax, 3)],
            "z": [round(bb.zmin, 3), round(bb.zmax, 3)],
        },
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_generation_preconditions() -> None:
    geometry_validation = load_json(GEOMETRY_VALIDATION)
    feasibility_validation = load_json(FEASIBILITY_VALIDATION)
    failures = []
    if geometry_validation.get("status") != "pass":
        failures.append(f"geometry contract validation is {geometry_validation.get('status')}")
    if feasibility_validation.get("status") != "pass":
        failures.append(f"selected-design feasibility validation is {feasibility_validation.get('status')}")
    if failures:
        raise RuntimeError("V29 sculpture generation blocked: " + "; ".join(failures))


def parts() -> dict[str, cq.Workplane]:
    carrier_local = union_all(
        [
            gear(54, 25.6, 27.6, -2.5, 2.5, tooth_width=1.8),
            annulus(42, 34, 2.0, 5.0),
            annulus(42, 34, -5.0, -2.0),
            box(72, 4, -2.0, 2.0),
            box(4, 72, -2.0, 2.0),
        ]
    )
    pallet_local = union_all([box(30, 3.2, -1.2, 1.2, -10, 8, -18), cyl(1.8, -1.5, 1.5, -18, 10)])
    base_with_supports = union_all(
        [
            cq.Workplane("XY").box(190, 130, 8).translate((0, 0, 4)),
            box(12, 18, 8, 44, -88, 0),
            box(12, 18, 8, 44, -72, 0),
            box(10, 18, 8, 24, -20, 0),
            box(10, 18, 8, 24, -4, 0),
            box(34, 12, 8, 18, -34, 0),
        ]
    )
    spatial_riser_bridge = union_all(
        [
            cyl(3, 20, 62),
            annulus(10, 3.2, 16, 24),
            annulus(10, 3.2, 58, 66),
            box(24, 24, 58, 66),
            canted(box(8, 64, -4, 4, 0, 0), center=(45, 0, 62)),
        ]
    )
    return {
        "01_base_plinth_v29": base_with_supports,
        "02_visible_winding_drum_v29": x_axis_gear(108, 41.5, 43.5, 8, -80, 0, 40, tooth_width=1.4),
        "03_spring_barrel_housing_v29": cq.Workplane("YZ").circle(18).extrude(18).translate((-42, 0, 20)),
        "04_horizontal_transfer_gear_v29": x_axis_gear(18, 8.2, 9.2, 8, -12, 0, 20, tooth_width=1.5),
        "05_spatial_riser_bridge_v29": spatial_riser_bridge,
        "06_vertical_riser_gear_v29": gear(20, 9.2, 10.2, 58, 64, tooth_width=1.6),
        "07_canted_carrier_drive_gear_v29": canted(gear(18, 8.2, 9.2, -3, 3, tooth_width=1.5), center=(45, 0, 62)),
        "08_fixed_internal_ring_72t_v29": canted(internal_gear(72, 40, 36.5, 35.0, -3, 3, tooth_width=1.3), center=(45, 0, 62)),
        "09_canted_carrier_frame_v29": canted(carrier_local),
        "10_orbit_escape_pinion_18t_v29": canted(gear(18, 8.2, 9.2, -3, 3, 27, 0, tooth_width=1.5)),
        "11_escape_wheel_v29": canted(gear(15, 6.3, 7.6, -1.5, 1.5, 27, 0, tooth_width=1.2)),
        "12_pallet_fork_v29": canted(pallet_local),
        "13_balance_wheel_v29": canted(union_all([annulus(13, 10, -1, 1), box(24, 1.6, -1, 1), box(1.6, 24, -1, 1)]), center=(45, 0, 62)),
    }


def mesh_payload(exports: list[dict]) -> list[dict]:
    role_map = {
        "01_base_plinth_v29": ("base", "#4d5964"),
        "02_visible_winding_drum_v29": ("visible_winding_drum", "#d39b35"),
        "03_spring_barrel_housing_v29": ("spring_barrel", "#a8792f"),
        "04_horizontal_transfer_gear_v29": ("horizontal_transfer", "#6f9fc1"),
        "05_spatial_riser_bridge_v29": ("spatial_riser", "#6f9fc1"),
        "06_vertical_riser_gear_v29": ("vertical_riser", "#7fb3d5"),
        "07_canted_carrier_drive_gear_v29": ("canted_drive", "#d87895"),
        "08_fixed_internal_ring_72t_v29": ("fixed_internal_ring", "#79a8c6"),
        "09_canted_carrier_frame_v29": ("carrier", "#d7a94c"),
        "10_orbit_escape_pinion_18t_v29": ("orbit_escape_pinion", "#e8792d"),
        "11_escape_wheel_v29": ("escape_wheel", "#ed8531"),
        "12_pallet_fork_v29": ("pallet_fork", "#e8e0d3"),
        "13_balance_wheel_v29": ("balance_wheel", "#f0d170"),
    }
    payload = []
    for item in exports:
        triangles = parse_ascii_stl(Path(item["stl"]))
        floats = [coord for tri in triangles for vertex in tri for coord in vertex]
        raw = struct.pack("<" + "f" * len(floats), *floats)
        role, color = role_map[item["name"]]
        payload.append(
            {
                "name": item["name"],
                "role": role,
                "color": color,
                "vertex_count": len(floats) // 3,
                "positions_b64": base64.b64encode(raw).decode("ascii"),
            }
        )
    return payload


def write_viewer(exports: list[dict]) -> None:
    payload = json.dumps(mesh_payload(exports), separators=(",", ":"))
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>V29 Spatial Sculpture Viewer</title>
<script type="module" src="https://unpkg.com/three@0.160.0/build/three.module.js"></script>
<style>body{{margin:0;background:#111820;color:#eef3f6;font-family:system-ui}}main{{display:grid;grid-template-columns:1fr 350px;min-height:100vh}}#stage{{height:100vh}}aside{{padding:16px;background:#18222d}}button{{margin:0 6px 8px 0}}input[type=range]{{width:100%}}.readout{{font-size:13px;line-height:1.45}}</style></head>
<body><main><section id="stage"></section><aside><h1>V29 Spatial Sculpture</h1><button id="play">Pause</button><button id="front">Front</button><button id="side">Side</button><button id="iso">Iso</button><button id="review">Review</button><p id="status" class="readout">Loading V29 CAD meshes...</p><label class="readout">Pose <input id="pose" type="range" min="0" max="360" step="15" value="0"></label><p id="ratioReadout" class="readout"></p><p id="claimNote" class="readout">Actual generated STL triangles are embedded. This is continuous fallback transform motion for a stationary-autonomous-winding spatial kinetic sculpture object candidate; the escapement is demonstrative and non-regulating, not watch-grade or native CAD animation.</p></aside></main>
<script type="application/json" id="meshData">{payload}</script>
<script type="module">
import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
const stage=document.getElementById('stage'), scene=new THREE.Scene();scene.background=new THREE.Color(0x111820);
const camera=new THREE.PerspectiveCamera(35,stage.clientWidth/stage.clientHeight,.1,1000);camera.position.set(180,-180,130);
const renderer=new THREE.WebGLRenderer({{antialias:true}});renderer.setSize(stage.clientWidth,stage.clientHeight);stage.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x22303d,2.2));const dl=new THREE.DirectionalLight(0xffffff,1.6);dl.position.set(100,-120,180);scene.add(dl);
const root=new THREE.Group();scene.add(root);const meshes=[];for(const p of JSON.parse(document.getElementById('meshData').textContent)){{const bytes=Uint8Array.from(atob(p.positions_b64),c=>c.charCodeAt(0));const arr=new Float32Array(bytes.buffer);const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(arr,3));g.computeVertexNormals();const m=new THREE.MeshStandardMaterial({{color:p.color,roughness:.55,metalness:.12,transparent:p.role==='base',opacity:p.role==='base'?.25:1}});const mesh=new THREE.Mesh(g,m);mesh.userData.role=p.role;mesh.userData.baseColor=p.color;mesh.userData.baseOpacity=p.role==='base'?.25:1;root.add(mesh);meshes.push(mesh)}}
document.getElementById('status').textContent=`Loaded V29 ${{meshes.length}} CAD mesh parts.`;
let yaw=-.95,pitch=.58,dist=230;function cam(){{camera.position.set(dist*Math.sin(yaw)*Math.cos(pitch),-dist*Math.cos(yaw)*Math.cos(pitch),dist*Math.sin(pitch));camera.lookAt(0,0,36)}}cam();for(const [id,v] of Object.entries({{front:[0,.35,220],side:[-1.57,.35,220],iso:[-.95,.58,230]}}))document.getElementById(id).onclick=()=>{{[yaw,pitch,dist]=v;cam()}};
let drag=false,lx=0,ly=0;renderer.domElement.onpointerdown=e=>{{drag=true;lx=e.clientX;ly=e.clientY}};renderer.domElement.onpointerup=()=>drag=false;renderer.domElement.onpointermove=e=>{{if(!drag)return;yaw-=(e.clientX-lx)*.006;pitch+=(e.clientY-ly)*.006;lx=e.clientX;ly=e.clientY;cam()}};renderer.domElement.onwheel=e=>{{e.preventDefault();dist*=1+Math.sign(e.deltaY)*.08;cam()}};
const reviewColors={{visible_winding_drum:'#ffd43b',horizontal_transfer:'#6ec5ff',vertical_riser:'#6ec5ff',carrier:'#ff9f43',orbit_escape_pinion:'#ff6b2d',escape_wheel:'#ff6b2d',pallet_fork:'#00e5ff',balance_wheel:'#fff176'}};
let reviewMode=false;function setReviewMode(enabled){{reviewMode=enabled;for(const mesh of meshes){{const role=mesh.userData.role;let opacity=mesh.userData.baseOpacity;if(enabled&&['base','spatial_riser','fixed_internal_ring'].includes(role))opacity=.15;mesh.material.color.set(enabled&&reviewColors[role]?reviewColors[role]:mesh.userData.baseColor);mesh.material.emissive.set(enabled&&reviewColors[role]?reviewColors[role]:'#000000');mesh.material.emissiveIntensity=enabled&&reviewColors[role]?0.35:0;mesh.material.transparent=opacity<1;mesh.material.opacity=opacity;mesh.material.depthWrite=!enabled||!['base','spatial_riser','fixed_internal_ring'].includes(role)}}}}document.getElementById('review').onclick=e=>{{setReviewMode(!reviewMode);e.target.textContent=reviewMode?'Solid':'Review'}};
const ratio=document.getElementById('ratioReadout'),pose=document.getElementById('pose');let running=true,theta=0;document.getElementById('play').onclick=e=>{{running=!running;e.target.textContent=running?'Pause':'Play'}};pose.oninput=()=>{{running=false;theta=THREE.MathUtils.degToRad(Number(pose.value));apply()}};
function apply(){{for(const m of meshes){{if(m.userData.role==='visible_winding_drum')m.rotation.x=theta; if(m.userData.role==='horizontal_transfer')m.rotation.x=-6*theta; if(m.userData.role==='vertical_riser')m.rotation.z=6*theta; if(m.userData.role==='carrier')m.rotation.z=-2*theta; if(m.userData.role==='orbit_escape_pinion'||m.userData.role==='escape_wheel')m.rotation.z=6*theta; if(m.userData.role==='balance_wheel')m.rotation.z=.35*Math.sin(8*theta); if(m.userData.role==='pallet_fork')m.rotation.z=.18*Math.sin(8*theta);}}const deg=((THREE.MathUtils.radToDeg(theta)%360)+360)%360;ratio.textContent=`drum ${{deg.toFixed(1)}} deg / transfer -6x / riser +6x / carrier -2x / fine motion 8x pulse`;}}
apply();let last=performance.now();function animate(now){{requestAnimationFrame(animate);const dt=(now-last)/1000;last=now;if(running)theta+=dt*.35;apply();renderer.render(scene,camera)}} requestAnimationFrame(animate);
window.__v29Debug={{setPoseDeg:(deg)=>{{running=false;theta=THREE.MathUtils.degToRad(deg);pose.value=String(deg);apply();renderer.render(scene,camera)}},play:()=>{{running=true}},pause:()=>{{running=false}},setReviewMode:(enabled)=>{{setReviewMode(enabled);renderer.render(scene,camera)}},getState:()=>({{thetaDeg:((THREE.MathUtils.radToDeg(theta)%360)+360)%360,yaw,pitch,dist,ratioText:ratio.textContent,reviewMode}}),setView:(view)=>{{document.getElementById(view).click();renderer.render(scene,camera)}}}};
</script></body></html>"""
    VIEWER.write_text(html, encoding="utf-8")


def write_contact_sheet(shape_map: dict[str, cq.Workplane]) -> None:
    colors = {
        "01_base_plinth_v29": (77, 89, 100),
        "02_visible_winding_drum_v29": (211, 155, 53),
        "03_spring_barrel_housing_v29": (168, 121, 47),
        "04_horizontal_transfer_gear_v29": (111, 159, 193),
        "05_spatial_riser_bridge_v29": (111, 159, 193),
        "06_vertical_riser_gear_v29": (127, 179, 213),
        "07_canted_carrier_drive_gear_v29": (216, 120, 149),
        "08_fixed_internal_ring_72t_v29": (121, 168, 198),
        "09_canted_carrier_frame_v29": (215, 169, 76),
        "10_orbit_escape_pinion_18t_v29": (232, 121, 45),
        "11_escape_wheel_v29": (237, 133, 49),
        "12_pallet_fork_v29": (232, 224, 211),
        "13_balance_wheel_v29": (240, 209, 112),
    }

    def render_colored(label: str, yaw: float, pitch: float) -> Image.Image:
        width, height = 420, 320
        tris = []
        projected_bounds = []
        for name, shape in shape_map.items():
            verts, faces = shape.val().tessellate(0.8, 0.25)
            rotated = [
                (
                    *rotate_xyz((v.x, v.y, v.z), yaw, pitch)[:2],
                    rotate_xyz((v.x, v.y, v.z), yaw, pitch)[2],
                )
                for v in verts
            ]
            projected_bounds.extend(rotated)
            for face in faces:
                tris.append((sum(rotated[index][2] for index in face) / 3.0, name, [rotated[index] for index in face]))
        xs = [p[0] for p in projected_bounds]
        ys = [p[1] for p in projected_bounds]
        span_x = max(xs) - min(xs) or 1.0
        span_y = max(ys) - min(ys) or 1.0
        scale = min((width - 36) / span_x, (height - 54) / span_y)
        x_mid = (max(xs) + min(xs)) / 2.0
        y_mid = (max(ys) + min(ys)) / 2.0

        def project(point: tuple[float, float, float]) -> tuple[int, int]:
            x, y, _ = point
            return (
                round(width / 2 + (x - x_mid) * scale),
                round(height / 2 - 4 - (y - y_mid) * scale),
            )

        panel = Image.new("RGB", (width, height), (18, 24, 32))
        draw = ImageDraw.Draw(panel)
        for _, name, points in sorted(tris):
            draw.polygon([project(point) for point in points], fill=colors[name])
        draw.rectangle((0, 0, width, 30), fill=(18, 24, 32))
        draw.text((12, 9), label, fill=(238, 243, 246))
        return panel

    panels = [
        render_colored("front oblique", 30, 18),
        render_colored("side spatial transition", 90, 10),
        render_colored("topology overview", 0, 70),
    ]
    sheet = Image.new("RGB", (420 * 3, 320), (18, 24, 32))
    for index, panel in enumerate(panels):
        sheet.paste(panel, (index * 420, 0))
    sheet.save(SHEET)


def write_csvs(exports: list[dict]) -> None:
    with (OUT / "printed_parts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["part", "qty"])
        w.writeheader()
        for item in exports:
            w.writerow({"part": item["name"], "qty": 1})
    with (OUT / "purchased_parts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["role", "item", "qty"])
        w.writeheader()
        w.writerows(
            [
                {"role": "winding_motor", "item": "20D 313:1 12V gearmotor family", "qty": 1},
                {"role": "energy_storage", "item": "LTML200Y 02 M torsion spring or equivalent", "qty": 1},
                {"role": "shafts", "item": "3 mm shaft stock", "qty": 4},
                {"role": "fasteners", "item": "M3 screws / washers", "qty": 8},
            ]
        )
    with (OUT / "assembly_sequence.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["step", "operation"])
        w.writeheader()
        for idx, op in enumerate(
            [
                "install base and power module",
                "install spring barrel and ratchet",
                "install transfer shaft and riser",
                "install canted carrier support",
                "install fine-motion train",
            ],
            start=1,
        ):
            w.writerow({"step": idx, "operation": op})


def main() -> int:
    assert_generation_preconditions()
    OUT.mkdir(parents=True, exist_ok=True)
    shape_map = parts()
    exports = [export(name, shape) for name, shape in shape_map.items()]
    write_viewer(exports)
    write_contact_sheet(shape_map)
    write_csvs(exports)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "claim": "first V29 local sculpture geometry package",
        "parts": exports,
        "viewer": str(VIEWER),
        "visibility_contact_sheet": str(SHEET),
        "evidence": {
            "stationary_autonomous_winding_evidence": "requires_audit",
            "spatial_drive_evidence": "requires_audit",
            "object_value_evidence": "requires_audit",
        },
    }
    SUMMARY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

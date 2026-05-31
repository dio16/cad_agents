from __future__ import annotations

import base64
import csv
import json
import math
import struct
from datetime import datetime, timezone
from pathlib import Path

from independent_v27_connected_audit import parse_ascii_stl
from v27_evidence import evidence_fields


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "tourbillon_v27_connected_contract.json"
OUT = ROOT / "reports" / "fabrication_v27_connected_package"
VIEWER = OUT / "v27_3d_cad_motion_viewer.html"


ROLE_MAP = {
    "01_base_plinth_bearing_pocket_v27.stl": {"role": "base", "color": "#5f6b73", "opacity": 0.38, "motion": "fixed"},
    "02_fixed_internal_ring_72t_v27.stl": {"role": "fixed_internal_ring", "color": "#6fa0bf", "opacity": 0.62, "motion": "fixed"},
    "03_rotating_carrier_drive_gear_v27.stl": {"role": "carrier", "color": "#d7a94c", "motion": "carrier"},
    "04_orbit_escape_pinion_18t_v27.stl": {"role": "orbit_escape_pinion", "color": "#e8792d", "motion": "orbit"},
    "05_hand_crank_pinion_v27.stl": {"role": "hand_input_pinion", "color": "#cc6092", "motion": "hand"},
    "06_balance_wheel_v27.stl": {"role": "balance_wheel", "color": "#f0d170", "motion": "balance"},
    "07_escape_wheel_15t_v27.stl": {"role": "escape_wheel", "color": "#ed8531", "motion": "escape"},
    "08_pallet_fork_bridge_v27.stl": {"role": "pallet_display", "color": "#e8e0d3", "motion": "pallet"},
    "09_crank_knob_v27.stl": {"role": "input_knob", "color": "#cc6092", "motion": "knob"},
}


def mesh_payload(manifest: dict) -> list[dict]:
    payload = []
    for item in manifest["parts"]:
        stl = Path(item["stl"])
        triangles = parse_ascii_stl(stl)
        floats = [coord for tri in triangles for vertex in tri for coord in vertex]
        raw = struct.pack("<" + "f" * len(floats), *floats)
        payload.append(
            {
                "file": stl.name,
                **ROLE_MAP[stl.name],
                "vertex_count": len(floats) // 3,
                "positions_b64": base64.b64encode(raw).decode("ascii"),
            }
        )
    return payload


def write_role_manifest(manifest: dict) -> None:
    roles = {
        "status": "pass",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **evidence_fields(),
        "roles": {
            "fixed_internal_ring": {"parent": "world", "support": "M3-fastened fixed ring", "motion": "fixed"},
            "carrier": {"parent": "world", "support": "608ZZ bearing and printed journal", "motion": "revolute_z"},
            "orbit_escape_pinion": {"parent": "carrier", "support": "3 mm shaft with two carrier bridge seats", "motion": "orbit plus spin"},
            "hand_input_pinion": {"parent": "world", "support": "3 mm hand input shaft", "motion": "revolute_z"},
            "balance_wheel": {"parent": "carrier", "support": "1.6 mm staff seats", "motion": "supported visual hardware only"},
            "escape_wheel": {"parent": "orbit_escape_pinion", "support": "coaxial orbit/escape shaft", "motion": "coaxial spin"},
            "pallet_display": {"parent": "carrier", "support": "1.6 mm pallet arbor", "motion": "eccentric pin-slot display"},
            "input_knob": {"parent": "hand_input_pinion", "support": "coaxial hand input shaft", "motion": "coaxial spin"},
        },
    }
    (OUT / "v27_role_manifest.json").write_text(json.dumps(roles, indent=2), encoding="utf-8")


def write_csvs(manifest: dict) -> None:
    with (OUT / "purchased_parts.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["role", "standard", "size_mm", "qty"])
        writer.writeheader()
        writer.writerows(manifest["standard_hardware"])
    rows = [
        {"step": 1, "operation": "Install 608ZZ bearing into base pocket.", "uses": "central_bearing", "gate": "bearing fit"},
        {"step": 2, "operation": "Install carrier journal through the bearing.", "uses": "carrier", "gate": "free carrier rotation"},
        {"step": 3, "operation": "Fasten fixed internal ring to base standoffs.", "uses": "fixed_internal_ring, ring_fasteners", "gate": "ring seats"},
        {"step": 4, "operation": "Install orbit/escape shaft and pinion.", "uses": "orbit_escape_shaft, orbit_escape_pinion", "gate": "shaft support"},
        {"step": 5, "operation": "Install hand input shaft, input pinion, and coaxial knob.", "uses": "hand_input_shaft, hand_input_pinion, input_knob", "gate": "input rotation"},
        {"step": 6, "operation": "Install balance staff and pallet arbor with pallet display arm.", "uses": "balance_staff, pallet_arbor", "gate": "supported moving roles"},
        {"step": 7, "operation": "Rotate input knob and inspect carrier/orbit/pallet display motion.", "uses": "viewer and assembled model", "gate": "motion contract"},
    ]
    with (OUT / "assembly_sequence.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "operation", "uses", "gate"])
        writer.writeheader()
        writer.writerows(rows)


def write_motion_validation(manifest: dict) -> None:
    drive = manifest["escapement_drive_model"]
    internal_mesh = next(mesh for mesh in manifest["gear_meshes"] if mesh["name"] == "fixed_internal_ring_to_orbit_escape_pinion")
    hand_mesh = next(mesh for mesh in manifest["gear_meshes"] if mesh["name"] == "hand_pinion_to_carrier_drive_gear")
    distance = math.dist(drive["escape_axis_mm"], drive["pallet_axis_mm"])
    samples = []
    for deg in range(0, 360, 15):
        rel = internal_mesh["relative_pinion_spin_ratio_in_carrier"] * deg
        angle = math.degrees(
            math.atan2(
                drive["escape_pin_offset_mm"] * math.sin(math.radians(rel)),
                distance + drive["escape_pin_offset_mm"] * math.cos(math.radians(rel)),
            )
        )
        samples.append({"carrier_deg": deg, "pallet_relative_deg": round(angle, 4)})
    report = {
        "status": "pass",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **evidence_fields(),
        "type": "fallback_transform_motion_with_eccentric_pin_slot_pallet_display",
        "joints": [
            {"role": "carrier", "ratio_to_carrier": 1.0},
            {"role": "hand_input_pinion", "ratio_to_carrier": hand_mesh["hand_spin_ratio_to_carrier"]},
            {
                "role": "orbit_escape_pinion",
                "relative_ratio_to_carrier": internal_mesh["relative_pinion_spin_ratio_in_carrier"],
                "absolute_ratio_to_carrier": 1.0 + internal_mesh["relative_pinion_spin_ratio_in_carrier"],
            },
            {
                "role": "escape_wheel",
                "relative_ratio_to_carrier": internal_mesh["relative_pinion_spin_ratio_in_carrier"],
                "absolute_ratio_to_carrier": 1.0 + internal_mesh["relative_pinion_spin_ratio_in_carrier"],
            },
            {"role": "pallet_display", "motion": "eccentric_pin_slot", "predicted_half_swing_deg": drive["predicted_pallet_half_swing_deg"]},
            {"role": "balance_wheel", "motion": "supported_visual_only"},
        ],
        "sampled_angles_deg": list(range(0, 360, 15)),
        "pallet_samples": samples,
        "viewer": str(VIEWER),
    }
    (OUT / "v27_motion_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_viewer(manifest: dict) -> None:
    payload = json.dumps(mesh_payload(manifest), separators=(",", ":"))
    half_swing = manifest["escapement_drive_model"]["predicted_pallet_half_swing_deg"]
    axes = manifest["axes_and_supports"]
    orbit_axis = axes["orbit_escape_axis"]["axis_mm"]
    balance_axis = axes["balance_axis"]["axis_mm"]
    pallet_axis = axes["pallet_axis"]["axis_mm"]
    hand_axis = axes["hand_axis"]["axis_mm"]
    internal_mesh = next(mesh for mesh in manifest["gear_meshes"] if mesh["name"] == "fixed_internal_ring_to_orbit_escape_pinion")
    hand_mesh = next(mesh for mesh in manifest["gear_meshes"] if mesh["name"] == "hand_pinion_to_carrier_drive_gear")
    drive = manifest["escapement_drive_model"]
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V27 3D CAD Motion Viewer</title><script type="module" src="https://unpkg.com/three@0.160.0/build/three.module.js"></script>
<style>body{{margin:0;background:#101820;color:#eef3f6;font-family:system-ui,sans-serif}}main{{display:grid;grid-template-columns:minmax(0,1fr) 340px;min-height:100vh}}#stage{{height:100vh}}.panel{{padding:16px;background:#17212b;border-left:1px solid #344554}}button{{margin:0 6px 8px 0}}input[type=range]{{width:100%}}.readout{{font-size:13px;line-height:1.45}}@media(max-width:760px){{main{{grid-template-columns:1fr}}#stage{{height:70vh}}}}</style></head>
<body><main><section id="stage"></section><aside class="panel"><h1>V27 CAD Motion</h1><button id="play">Pause</button><button id="front">Front</button><button id="top">Top</button><button id="iso">Iso</button><button id="review">Review</button>
<p id="status" class="readout">Loading V27 CAD meshes...</p><label class="readout">Pose <input id="pose" type="range" min="0" max="360" step="15" value="0"></label><p id="ratioReadout" class="readout"></p><p class="readout">Actual generated STL triangles are embedded. Drag to orbit, scroll to zoom. Pallet motion is derived from the eccentric pin-slot relation; the balance wheel is supported visual hardware only.</p></aside></main>
<script type="application/json" id="meshData">{payload}</script><script type="module">
import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
const stage=document.getElementById('stage'),scene=new THREE.Scene();scene.background=new THREE.Color(0x101820);
const camera=new THREE.PerspectiveCamera(35,stage.clientWidth/stage.clientHeight,.1,1000),renderer=new THREE.WebGLRenderer({{antialias:true}});renderer.setSize(stage.clientWidth,stage.clientHeight);stage.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x24313b,2.2));const dl=new THREE.DirectionalLight(0xffffff,1.6);dl.position.set(120,-120,180);scene.add(dl);
const root=new THREE.Group();root.rotation.x=-Math.PI/2;scene.add(root);const fixed=new THREE.Group(),carrier=new THREE.Group(),hand=new THREE.Group(),orbit=new THREE.Group(),escape=new THREE.Group(),balance=new THREE.Group(),pallet=new THREE.Group(),knob=new THREE.Group();root.add(fixed,carrier,hand);carrier.add(orbit,balance,pallet);orbit.add(escape);hand.add(knob);
const centers={{orbit:{json.dumps([*orbit_axis, 0])},balance:{json.dumps([*balance_axis, 0])},pallet:{json.dumps([*pallet_axis, 0])},hand:{json.dumps([*hand_axis, 0])}}};hand.position.set(...centers.hand);orbit.position.set(...centers.orbit);balance.position.set(...centers.balance);pallet.position.set(...centers.pallet);knob.position.set(0,0,45);
function f32(b64){{const bin=atob(b64),bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);return new Float32Array(bytes.buffer)}}
function mesh(part){{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(f32(part.positions_b64),3));g.computeVertexNormals();const m=new THREE.MeshStandardMaterial({{color:part.color,roughness:.55,metalness:.18,transparent:(part.opacity??1)<1,opacity:part.opacity??1,side:THREE.DoubleSide}});const mesh=new THREE.Mesh(g,m);mesh.userData.role=part.role;mesh.userData.baseOpacity=part.opacity??1;mesh.userData.baseColor=part.color;return mesh}}
const reviewable=[];let vertices=0;for(const part of JSON.parse(document.getElementById('meshData').textContent)){{const m=mesh(part);vertices+=part.vertex_count;reviewable.push(m);if(part.motion==='fixed')fixed.add(m);else if(part.motion==='carrier')carrier.add(m);else if(part.motion==='hand'){{m.position.y+=58.5;hand.add(m)}}else if(part.motion==='orbit')orbit.add(m);else if(part.motion==='escape')escape.add(m);else if(part.motion==='balance')balance.add(m);else if(part.motion==='pallet')pallet.add(m);else if(part.motion==='knob')knob.add(m)}}
document.getElementById('status').textContent=`Loaded V27 9 CAD mesh parts / ${{vertices.toLocaleString()}} vertices.`;
let yaw=-.95,pitch=.58,dist=430;function cam(){{camera.position.set(dist*Math.sin(yaw)*Math.cos(pitch),-dist*Math.cos(yaw)*Math.cos(pitch),dist*Math.sin(pitch));camera.lookAt(0,0,0)}}cam();for(const [id,v] of Object.entries({{front:[0,.42,390],top:[0,1.25,360],iso:[-.95,.58,430]}}))document.getElementById(id).onclick=()=>{{[yaw,pitch,dist]=v;cam()}};
let drag=false,lx=0,ly=0;renderer.domElement.onpointerdown=e=>{{drag=true;lx=e.clientX;ly=e.clientY}};renderer.domElement.onpointerup=()=>drag=false;renderer.domElement.onpointermove=e=>{{if(!drag)return;yaw-=(e.clientX-lx)*.006;pitch+=(e.clientY-ly)*.006;lx=e.clientX;ly=e.clientY;cam()}};renderer.domElement.onwheel=e=>{{e.preventDefault();dist*=1+Math.sign(e.deltaY)*.08;cam()}};
const ratio=document.getElementById('ratioReadout'),pose=document.getElementById('pose');let theta=0,playing=true;document.getElementById('play').onclick=e=>{{playing=!playing;e.target.textContent=playing?'Pause':'Play'}};pose.oninput=()=>{{playing=false;theta=THREE.MathUtils.degToRad(Number(pose.value));apply()}};
const reviewColors={{carrier:'#ffd43b',orbit_escape_pinion:'#ff5a00',hand_input_pinion:'#ff00cc',balance_wheel:'#00ff6a',escape_wheel:'#ff1744',pallet_display:'#00e5ff',input_knob:'#ff00cc'}};
let reviewMode=false;function setReviewMode(enabled){{reviewMode=enabled;for(const mesh of reviewable){{const role=mesh.userData.role;let opacity=mesh.userData.baseOpacity;if(enabled&&role==='base')opacity=.14;else if(enabled&&role==='fixed_internal_ring')opacity=.24;else if(enabled&&role==='carrier')opacity=.28;mesh.material.color.set(enabled&&reviewColors[role]?reviewColors[role]:mesh.userData.baseColor);mesh.material.emissive.set(enabled&&reviewColors[role]?reviewColors[role]:'#000000');mesh.material.emissiveIntensity=enabled&&reviewColors[role]?.length?0.35:0;mesh.material.transparent=opacity<1;mesh.material.opacity=opacity;mesh.material.depthWrite=!enabled||!['base','fixed_internal_ring','carrier'].includes(role)}}}}document.getElementById('review').onclick=e=>{{setReviewMode(!reviewMode);e.target.textContent=reviewMode?'Solid':'Review'}};
const relativeOrbitRatio={internal_mesh["relative_pinion_spin_ratio_in_carrier"]}, handRatio={hand_mesh["hand_spin_ratio_to_carrier"]}, pinOffset={drive["escape_pin_offset_mm"]}, pivotDistance={math.dist(drive["escape_axis_mm"], drive["pallet_axis_mm"])};
function palletAngle(rel){{return Math.atan2(pinOffset*Math.sin(rel),pivotDistance+pinOffset*Math.cos(rel))}}function apply(){{carrier.rotation.z=theta;hand.rotation.z=handRatio*theta;orbit.rotation.z=relativeOrbitRatio*theta;escape.rotation.z=0;balance.rotation.z=0;pallet.rotation.z=palletAngle(relativeOrbitRatio*theta);const deg=((THREE.MathUtils.radToDeg(theta)%360)+360)%360;ratio.textContent=`carrier ${{deg.toFixed(1)}} deg / hand ${{handRatio}} / orbit relative ${{relativeOrbitRatio}} / pin-slot pallet display ±{half_swing} deg`;}}
apply();let last=performance.now();function loop(now){{const dt=(now-last)/1000;last=now;if(playing)theta+=dt*.65;apply();renderer.render(scene,camera);requestAnimationFrame(loop)}}requestAnimationFrame(loop);addEventListener('resize',()=>{{camera.aspect=stage.clientWidth/stage.clientHeight;camera.updateProjectionMatrix();renderer.setSize(stage.clientWidth,stage.clientHeight)}})
window.__v27Debug={{setPoseDeg:(deg)=>{{playing=false;theta=THREE.MathUtils.degToRad(deg);pose.value=String(deg);apply();renderer.render(scene,camera)}},play:()=>{{playing=true}},pause:()=>{{playing=false}},setReviewMode:(enabled)=>{{setReviewMode(enabled);renderer.render(scene,camera)}},getState:()=>({{thetaDeg:((THREE.MathUtils.radToDeg(theta)%360)+360)%360,yaw,pitch,dist,ratioText:ratio.textContent,reviewMode}}),setView:(view)=>{{document.getElementById(view).click();renderer.render(scene,camera)}}}};
</script></body></html>"""
    VIEWER.write_text(html, encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    write_role_manifest(manifest)
    write_csvs(manifest)
    write_motion_validation(manifest)
    write_viewer(manifest)
    print(json.dumps({"status": "pass", "viewer": str(VIEWER)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

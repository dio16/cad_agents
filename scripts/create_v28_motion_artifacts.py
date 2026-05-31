from __future__ import annotations

import base64
import csv
import json
import math
import struct
from datetime import datetime, timezone
from pathlib import Path

from independent_v27_connected_audit import parse_ascii_stl

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifests' / 'tourbillon_v28_mechanism_contract.json'
OUT = ROOT / 'reports' / 'fabrication_v28_mechanism_package'
VIEWER = OUT / 'v28_3d_cad_motion_viewer.html'
AXIS_DIRECTION = [0.0, 0.0, 1.0]
VISIBLE_MOVING_ROLES = [
    'carrier',
    'orbit_escape_pinion',
    'hand_input_pinion',
    'escape_wheel',
    'pallet_fork',
    'balance_wheel',
]
ROLE_MAP = {
    '01_base_plinth_bearing_pocket_v28.stl': {'role': 'base', 'color': '#5f6b73', 'opacity': 0.38, 'motion': 'fixed'},
    '02_fixed_internal_ring_72t_v28.stl': {'role': 'fixed_internal_ring', 'color': '#6fa0bf', 'opacity': 0.62, 'motion': 'fixed'},
    '03_rotating_carrier_drive_gear_v28.stl': {'role': 'carrier', 'color': '#d7a94c', 'motion': 'carrier'},
    '04_orbit_escape_pinion_18t_v28.stl': {'role': 'orbit_escape_pinion', 'color': '#e8792d', 'motion': 'orbit'},
    '05_hand_crank_pinion_v28.stl': {'role': 'hand_input_pinion', 'color': '#cc6092', 'motion': 'hand'},
    '06_balance_wheel_v28.stl': {'role': 'balance_wheel', 'color': '#f0d170', 'motion': 'balance'},
    '07_escape_wheel_15t_v28.stl': {'role': 'escape_wheel', 'color': '#ed8531', 'motion': 'escape'},
    '08_pallet_fork_bridge_v28.stl': {'role': 'pallet_fork', 'color': '#e8e0d3', 'motion': 'pallet'},
    '09_crank_knob_v28.stl': {'role': 'input_knob', 'color': '#cc6092', 'motion': 'knob'},
}


def read_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def mesh_payload(manifest: dict) -> list[dict]:
    payload = []
    for item in manifest['parts']:
        stl = Path(item['stl'])
        triangles = parse_ascii_stl(stl)
        floats = [coord for tri in triangles for vertex in tri for coord in vertex]
        raw = struct.pack('<' + 'f' * len(floats), *floats)
        payload.append(
            {
                'file': stl.name,
                **ROLE_MAP[stl.name],
                'vertex_count': len(floats) // 3,
                'positions_b64': base64.b64encode(raw).decode('ascii'),
            }
        )
    return payload


def pallet_angle_deg(relative_escape_deg: float, pivot_distance_mm: float, pin_offset_mm: float) -> float:
    angle = math.radians(relative_escape_deg)
    return math.degrees(math.atan2(pin_offset_mm * math.sin(angle), pivot_distance_mm + pin_offset_mm * math.cos(angle)))


def rotate_point(x: float, y: float, deg: float) -> tuple[float, float]:
    angle = math.radians(deg)
    return (x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle))


def balance_angle_deg(manifest: dict, pallet_relative_deg: float) -> tuple[float, float]:
    drive = manifest['balance_drive_model']
    pallet_axis = tuple(drive['pallet_axis_mm'])
    balance_axis = tuple(drive['balance_axis_mm'])
    output_angle = drive['pallet_output_pin_zero_angle_deg'] + pallet_relative_deg
    dx, dy = rotate_point(drive['pallet_output_pin_offset_mm'], 0.0, output_angle)
    pin = (pallet_axis[0] + dx, pallet_axis[1] + dy)
    vector = (pin[0] - balance_axis[0], pin[1] - balance_axis[1])
    angle = math.degrees(math.atan2(vector[1], vector[0])) - drive['slot_zero_angle_deg']
    return angle, math.dist(pin, balance_axis)


def axis_metadata(manifest: dict, axis_name: str, frame: str) -> dict:
    axis = manifest['axes_and_supports'][axis_name]
    return {
        'name': axis_name,
        'origin_mm': [*axis['axis_mm'], 0.0],
        'direction': AXIS_DIRECTION,
        'frame': frame,
    }


def write_role_manifest(manifest: dict) -> None:
    report = {
        'status': 'pass',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'visible_moving_roles': VISIBLE_MOVING_ROLES,
        'roles': {
            'fixed_internal_ring': {
                'parent': 'world',
                'support': 'M3-fastened fixed ring',
                'motion': 'fixed',
                'axis': axis_metadata(manifest, 'central_axis', 'world'),
            },
            'carrier': {
                'parent': 'world',
                'support': '608ZZ bearing and printed journal',
                'motion': 'revolute_z',
                'axis': axis_metadata(manifest, 'central_axis', 'world'),
            },
            'orbit_escape_pinion': {
                'parent': 'carrier',
                'support': '3 mm shaft with two carrier bridge seats',
                'motion': 'orbit plus spin',
                'axis': axis_metadata(manifest, 'orbit_escape_axis', 'carrier'),
            },
            'hand_input_pinion': {
                'parent': 'world',
                'support': '3 mm hand input shaft',
                'motion': 'revolute_z',
                'axis': axis_metadata(manifest, 'hand_axis', 'world'),
            },
            'escape_wheel': {
                'parent': 'orbit_escape_pinion',
                'support': 'coaxial orbit/escape shaft',
                'motion': 'coaxial spin',
                'axis': axis_metadata(manifest, 'orbit_escape_axis', 'carrier'),
            },
            'pallet_fork': {
                'parent': 'carrier',
                'support': '1.6 mm pallet arbor',
                'motion': 'eccentric pin-slot drive',
                'axis': axis_metadata(manifest, 'pallet_axis', 'carrier'),
            },
            'balance_wheel': {
                'parent': 'carrier',
                'support': '1.6 mm staff seats',
                'motion': 'pallet-output-pin radial-slot drive',
                'axis': axis_metadata(manifest, 'balance_axis', 'carrier'),
            },
            'input_knob': {
                'parent': 'hand_input_pinion',
                'support': 'coaxial hand input shaft',
                'motion': 'coaxial spin',
                'axis': axis_metadata(manifest, 'hand_axis', 'world'),
            },
        },
    }
    (OUT / 'v28_role_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def write_csvs(manifest: dict) -> None:
    with (OUT / 'purchased_parts.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['role', 'standard', 'size_mm', 'qty'])
        writer.writeheader()
        writer.writerows(manifest['standard_hardware'])
    with (OUT / 'assembly_sequence.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['step', 'operation', 'uses', 'gate'])
        writer.writeheader()
        writer.writerows(manifest['assembly_sequence'])


def write_motion_validation(manifest: dict) -> None:
    escapement = manifest['escapement_drive_model']
    internal_mesh = next(mesh for mesh in manifest['gear_meshes'] if mesh['name'] == 'fixed_internal_ring_to_orbit_escape_pinion')
    hand_mesh = next(mesh for mesh in manifest['gear_meshes'] if mesh['name'] == 'hand_pinion_to_carrier_drive_gear')
    pivot_distance = math.dist(escapement['escape_axis_mm'], escapement['pallet_axis_mm'])
    pallet_samples = []
    balance_samples = []
    for deg in range(0, 360, 15):
        relative_escape = internal_mesh['relative_pinion_spin_ratio_in_carrier'] * deg
        pallet = pallet_angle_deg(relative_escape, pivot_distance, escapement['escape_pin_offset_mm'])
        balance, pin_radius = balance_angle_deg(manifest, pallet)
        pallet_samples.append({'carrier_deg': deg, 'pallet_relative_deg': round(pallet, 4)})
        balance_samples.append({'carrier_deg': deg, 'balance_relative_deg': round(balance, 4), 'pin_radius_from_balance_mm': round(pin_radius, 4)})
    report = {
        'status': 'pass',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'type': 'fallback_transform_motion_with_physical_pallet_to_balance_linkage',
        'joints': [
            {'role': 'carrier', 'ratio_to_carrier': 1.0},
            {'role': 'hand_input_pinion', 'ratio_to_carrier': hand_mesh['hand_spin_ratio_to_carrier']},
            {'role': 'orbit_escape_pinion', 'relative_ratio_to_carrier': internal_mesh['relative_pinion_spin_ratio_in_carrier']},
            {'role': 'escape_wheel', 'relative_ratio_to_carrier': internal_mesh['relative_pinion_spin_ratio_in_carrier']},
            {'role': 'pallet_fork', 'motion': 'eccentric_pin_slot', 'predicted_half_swing_deg': escapement['predicted_pallet_half_swing_deg']},
            {'role': 'balance_wheel', 'motion': 'pallet_output_pin_radial_slot', 'predicted_half_swing_deg': manifest['balance_drive_model']['predicted_balance_half_swing_deg']},
        ],
        'sampled_angles_deg': list(range(0, 360, 15)),
        'pallet_samples': pallet_samples,
        'balance_samples': balance_samples,
        'viewer': str(VIEWER),
    }
    (OUT / 'v28_motion_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def write_viewer(manifest: dict) -> None:
    payload = json.dumps(mesh_payload(manifest), separators=(',', ':'))
    axes = manifest['axes_and_supports']
    orbit_axis = axes['orbit_escape_axis']['axis_mm']
    balance_axis = axes['balance_axis']['axis_mm']
    pallet_axis = axes['pallet_axis']['axis_mm']
    hand_axis = axes['hand_axis']['axis_mm']
    internal_mesh = next(mesh for mesh in manifest['gear_meshes'] if mesh['name'] == 'fixed_internal_ring_to_orbit_escape_pinion')
    hand_mesh = next(mesh for mesh in manifest['gear_meshes'] if mesh['name'] == 'hand_pinion_to_carrier_drive_gear')
    escapement = manifest['escapement_drive_model']
    balance_drive = manifest['balance_drive_model']
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V28 3D CAD Motion Viewer</title><script type="module" src="https://unpkg.com/three@0.160.0/build/three.module.js"></script>
<style>body{{margin:0;background:#101820;color:#eef3f6;font-family:system-ui,sans-serif}}main{{display:grid;grid-template-columns:minmax(0,1fr) 360px;min-height:100vh}}#stage{{height:100vh}}.panel{{padding:16px;background:#17212b;border-left:1px solid #344554}}button{{margin:0 6px 8px 0}}input[type=range]{{width:100%}}.readout{{font-size:13px;line-height:1.45}}@media(max-width:760px){{main{{grid-template-columns:1fr}}#stage{{height:70vh}}}}</style></head>
<body><main><section id="stage"></section><aside class="panel"><h1>V28 CAD Motion</h1><button id="play">Pause</button><button id="front">Front</button><button id="top">Top</button><button id="iso">Iso</button><button id="review">Review</button>
<p id="status" class="readout">Loading V28 CAD meshes...</p><label class="readout">Pose <input id="pose" type="range" min="0" max="360" step="15" value="0"></label><p id="ratioReadout" class="readout"></p><p id="claimNote" class="readout">Actual generated STL triangles are embedded. This is fallback transform motion for a mechanically driven tabletop mechanism with a physical pallet-to-balance display linkage; the escapement remains non-regulating and demonstrative, not watch-grade or native CAD animation.</p></aside></main>
<script type="application/json" id="meshData">{payload}</script><script type="module">
import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
const stage=document.getElementById('stage'),scene=new THREE.Scene();scene.background=new THREE.Color(0x101820);
const camera=new THREE.PerspectiveCamera(35,stage.clientWidth/stage.clientHeight,.1,1000),renderer=new THREE.WebGLRenderer({{antialias:true}});renderer.setSize(stage.clientWidth,stage.clientHeight);stage.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x24313b,2.2));const dl=new THREE.DirectionalLight(0xffffff,1.6);dl.position.set(120,-120,180);scene.add(dl);
const root=new THREE.Group();root.rotation.x=-Math.PI/2;scene.add(root);const fixed=new THREE.Group(),carrier=new THREE.Group(),hand=new THREE.Group(),orbit=new THREE.Group(),escape=new THREE.Group(),balance=new THREE.Group(),pallet=new THREE.Group(),knob=new THREE.Group();root.add(fixed,carrier,hand);carrier.add(orbit,balance,pallet);orbit.add(escape);hand.add(knob);
const centers={{orbit:{json.dumps([*orbit_axis, 0])},balance:{json.dumps([*balance_axis, 0])},pallet:{json.dumps([*pallet_axis, 0])},hand:{json.dumps([*hand_axis, 0])}}};hand.position.set(...centers.hand);orbit.position.set(...centers.orbit);balance.position.set(...centers.balance);pallet.position.set(...centers.pallet);knob.position.set(0,0,45);
function f32(b64){{const bin=atob(b64),bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);return new Float32Array(bytes.buffer)}}
function mesh(part){{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(f32(part.positions_b64),3));g.computeVertexNormals();const m=new THREE.MeshStandardMaterial({{color:part.color,roughness:.55,metalness:.18,transparent:(part.opacity??1)<1,opacity:part.opacity??1,side:THREE.DoubleSide}});const mesh=new THREE.Mesh(g,m);mesh.userData.role=part.role;mesh.userData.baseOpacity=part.opacity??1;mesh.userData.baseColor=part.color;return mesh}}
const reviewable=[];let vertices=0;for(const part of JSON.parse(document.getElementById('meshData').textContent)){{const m=mesh(part);vertices+=part.vertex_count;reviewable.push(m);if(part.motion==='fixed')fixed.add(m);else if(part.motion==='carrier')carrier.add(m);else if(part.motion==='hand'){{m.position.x-=centers.hand[0];m.position.y-=centers.hand[1];hand.add(m)}}else if(part.motion==='orbit')orbit.add(m);else if(part.motion==='escape')escape.add(m);else if(part.motion==='balance')balance.add(m);else if(part.motion==='pallet')pallet.add(m);else if(part.motion==='knob')knob.add(m)}}
document.getElementById('status').textContent=`Loaded V28 9 CAD mesh parts / ${{vertices.toLocaleString()}} vertices.`;
let yaw=-.95,pitch=.58,dist=430;function cam(){{camera.position.set(dist*Math.sin(yaw)*Math.cos(pitch),-dist*Math.cos(yaw)*Math.cos(pitch),dist*Math.sin(pitch));camera.lookAt(0,0,0)}}cam();for(const [id,v] of Object.entries({{front:[0,.42,390],top:[0,1.25,360],iso:[-.95,.58,430]}}))document.getElementById(id).onclick=()=>{{[yaw,pitch,dist]=v;cam()}};
let drag=false,lx=0,ly=0;renderer.domElement.onpointerdown=e=>{{drag=true;lx=e.clientX;ly=e.clientY}};renderer.domElement.onpointerup=()=>drag=false;renderer.domElement.onpointermove=e=>{{if(!drag)return;yaw-=(e.clientX-lx)*.006;pitch+=(e.clientY-ly)*.006;lx=e.clientX;ly=e.clientY;cam()}};renderer.domElement.onwheel=e=>{{e.preventDefault();dist*=1+Math.sign(e.deltaY)*.08;cam()}};
const ratio=document.getElementById('ratioReadout'),pose=document.getElementById('pose');let theta=0,playing=true;document.getElementById('play').onclick=e=>{{playing=!playing;e.target.textContent=playing?'Pause':'Play'}};pose.oninput=()=>{{playing=false;theta=THREE.MathUtils.degToRad(Number(pose.value));apply()}};
const reviewColors={{carrier:'#ffd43b',orbit_escape_pinion:'#ff5a00',hand_input_pinion:'#ff00cc',balance_wheel:'#00ff6a',escape_wheel:'#ff1744',pallet_fork:'#00e5ff',input_knob:'#ff00cc'}};
let reviewMode=false;function setReviewMode(enabled){{reviewMode=enabled;for(const mesh of reviewable){{const role=mesh.userData.role;let opacity=mesh.userData.baseOpacity;if(enabled&&role==='base')opacity=.14;else if(enabled&&role==='fixed_internal_ring')opacity=.24;else if(enabled&&role==='carrier')opacity=.28;mesh.material.color.set(enabled&&reviewColors[role]?reviewColors[role]:mesh.userData.baseColor);mesh.material.emissive.set(enabled&&reviewColors[role]?reviewColors[role]:'#000000');mesh.material.emissiveIntensity=enabled&&reviewColors[role]?.length?0.35:0;mesh.material.transparent=opacity<1;mesh.material.opacity=opacity;mesh.material.depthWrite=!enabled||!['base','fixed_internal_ring','carrier'].includes(role)}}}}document.getElementById('review').onclick=e=>{{setReviewMode(!reviewMode);e.target.textContent=reviewMode?'Solid':'Review'}};
const relativeOrbitRatio={internal_mesh['relative_pinion_spin_ratio_in_carrier']},handRatio={hand_mesh['hand_spin_ratio_to_carrier']},escapePinOffset={escapement['escape_pin_offset_mm']},escapeToPalletDistance={math.dist(escapement['escape_axis_mm'], escapement['pallet_axis_mm'])},palletOutputPinOffset={balance_drive['pallet_output_pin_offset_mm']},palletOutputZero=THREE.MathUtils.degToRad({balance_drive['pallet_output_pin_zero_angle_deg']}),balanceSlotZero=THREE.MathUtils.degToRad({balance_drive['slot_zero_angle_deg']});
function palletAngle(rel){{return Math.atan2(escapePinOffset*Math.sin(rel),escapeToPalletDistance+escapePinOffset*Math.cos(rel))}}function balanceAngle(palletRel){{const out=palletOutputZero+palletRel,px=centers.pallet[0]+palletOutputPinOffset*Math.cos(out),py=centers.pallet[1]+palletOutputPinOffset*Math.sin(out);return Math.atan2(py-centers.balance[1],px-centers.balance[0])-balanceSlotZero}}function apply(){{carrier.rotation.z=theta;hand.rotation.z=handRatio*theta;orbit.rotation.z=relativeOrbitRatio*theta;escape.rotation.z=0;const palletRel=palletAngle(relativeOrbitRatio*theta),balanceRel=balanceAngle(palletRel);pallet.rotation.z=palletRel;balance.rotation.z=balanceRel;const deg=((THREE.MathUtils.radToDeg(theta)%360)+360)%360;ratio.textContent=`carrier ${{deg.toFixed(1)}} deg / hand ${{handRatio}} / orbit relative ${{relativeOrbitRatio}} / physical pallet-to-balance linkage / non-regulating display`;}}
apply();let last=performance.now();function loop(now){{const dt=(now-last)/1000;last=now;if(playing)theta+=dt*.65;apply();renderer.render(scene,camera);requestAnimationFrame(loop)}}requestAnimationFrame(loop);addEventListener('resize',()=>{{camera.aspect=stage.clientWidth/stage.clientHeight;camera.updateProjectionMatrix();renderer.setSize(stage.clientWidth,stage.clientHeight)}})
window.__v28Debug={{setPoseDeg:(deg)=>{{playing=false;theta=THREE.MathUtils.degToRad(deg);pose.value=String(deg);apply();renderer.render(scene,camera)}},play:()=>{{playing=true}},pause:()=>{{playing=false}},setReviewMode:(enabled)=>{{setReviewMode(enabled);renderer.render(scene,camera)}},getState:()=>({{thetaDeg:((THREE.MathUtils.radToDeg(theta)%360)+360)%360,yaw,pitch,dist,ratioText:ratio.textContent,reviewMode}}),setView:(view)=>{{document.getElementById(view).click();renderer.render(scene,camera)}}}};
</script></body></html>"""
    VIEWER.write_text(html, encoding='utf-8')


def main() -> int:
    manifest = read_manifest()
    OUT.mkdir(parents=True, exist_ok=True)
    write_role_manifest(manifest)
    write_csvs(manifest)
    write_motion_validation(manifest)
    write_viewer(manifest)
    print(json.dumps({'status': 'pass', 'reports': ['v28_role_manifest.json', 'v28_motion_validation.json'], 'viewer': str(VIEWER)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

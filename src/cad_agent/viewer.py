"""Self-contained HTML assembly viewer for human review.

The deterministic CAD runtime (``run_cad_runtime``) emits STEP / STL artifacts. The
STEP file is a metadata placeholder; the STL file carries the actual mesh geometry
(real cadquery/OpenCASCADE mesh when available, otherwise a surrogate box mesh). This
viewer renders the **actual STL triangles** of every part so what a human sees matches
the generated artifact, then places each part at its assembly location. It is the
standard human-review artifact produced by the assembly pipeline
(see :func:`cad_agent.platform_poc.run_assembly_pipeline`).

The output is a single, dependency-free HTML file (no CDN, no network) using a small
Canvas2D 3D triangle renderer. Known limitation: surrogate CAD produces simplified box
meshes, not true gear teeth; the viewer faithfully shows whatever the STL contains.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

SHAFT_COLORS = (
    "#4e79a7",
    "#f28e2b",
    "#59a14f",
    "#e15759",
    "#76b7b2",
    "#b07aa1",
    "#edc948",
    "#9c755f",
)


def _esc(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _hash_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def read_stl_triangles(path: Path) -> list[list[list[float]]]:
    """Parse an STL file (ASCII or binary) into a list of triangles (each 3 vertices)."""
    data = Path(path).read_bytes()
    stripped = data.lstrip()
    if stripped[:5].lower() == b"solid":
        return _read_stl_ascii(data)
    if len(data) >= 84:
        count = struct.unpack("<I", data[80:84])[0]
        if len(data) == 84 + count * 50:
            return _read_stl_binary(data, count)
    return _read_stl_ascii(data)


def _read_stl_binary(data: bytes, count: int) -> list[list[list[float]]]:
    tris: list[list[list[float]]] = []
    off = 84
    for _ in range(count):
        vals = struct.unpack("<12f", data[off : off + 48])
        off += 48
        tris.append(
            [
                [vals[3], vals[4], vals[5]],
                [vals[6], vals[7], vals[8]],
                [vals[9], vals[10], vals[11]],
            ]
        )
        off += 2
    return tris


def _read_stl_ascii(data: bytes) -> list[list[list[float]]]:
    text = data.decode("utf-8", errors="ignore")
    tris: list[list[list[float]]] = []
    verts: list[list[float]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "vertex":
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
            if len(verts) == 3:
                tris.append(verts)
                verts = []
    return tris


def box_mesh(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> list[list[list[float]]]:
    """Fallback: build the 12 triangles of an axis-aligned box (used when no STL exists)."""
    v = [
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ]
    quads = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [3, 2, 6, 7], [0, 3, 7, 4], [1, 2, 6, 5]]
    tris: list[list[list[float]]] = []
    for q in quads:
        a, b, c, d = (v[i] for i in q)
        tris.append([a, b, c])
        tris.append([a, c, d])
    return tris


def triangles_bbox(tris: list[list[list[float]]]) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for tri in tris:
        for v in tri:
            xs.append(v[0])
            ys.append(v[1])
            zs.append(v[2])
    return ([min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)])


def _build_data(
    parts: list[Any],
    report: Any,
    spec: dict[str, Any],
    requirement: dict[str, Any],
    ratio: float | None,
) -> dict[str, Any]:
    part_data: list[dict[str, Any]] = []
    for part in parts:
        tris = part.triangles
        (lmin, lmax) = triangles_bbox(tris)
        part_data.append(
            {
                "id": part.part_id,
                "color": part.color,
                "triangles": tris,
                "center": [(lmin[0] + lmax[0]) / 2.0, (lmin[1] + lmax[1]) / 2.0, (lmin[2] + lmax[2]) / 2.0],
            }
        )

    centers: set[tuple[float, float]] = set()
    for p in part_data:
        c = p["center"]
        centers.add((round(c[0], 3), round(c[1], 3)))
    shafts = [[cx, cy] for cx, cy in sorted(centers)]

    summary = (
        "<p><b>製品種別:</b> "
        + _esc(requirement.get("product_type", "assembly"))
        + "</p><ul>"
        + "".join(f"<li>{_esc(item)}</li>" for item in requirement.get("functional_requirements", []))
        + "</ul>"
    )
    limitations = (
        "<ul>"
        + "".join(f"<li>{_esc(item)}</li>" for item in spec.get("unresolved_risks", []))
        + "</ul><p>※ 各ギアは run_cad_runtime が出力した STL メッシュ（成果物そのものの幾何）を描画します。STEP はメタデータ placeholder のため STL を可視化します。Surrogate CAD の場合は簡易ボックスメッシュとなります。</p>"
    )

    return {
        "title": f"Assembly Viewer: {_esc(requirement.get('product_type', 'assembly'))}",
        "parts": part_data,
        "shafts": shafts,
        "ratio": ratio,
        "status": getattr(report, "status", "unknown"),
        "summary": summary,
        "limitations": limitations,
    }


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{
  --bg:#0f1420; --panel:#171d2b; --panel-2:#1f2738; --text:#e6ebf2; --muted:#8b96a8;
  --accent:#4f8cff; --ok:#2ecc71; --bad:#ff5c5c; --border:#2a3346;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%;font-family:-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;background:var(--bg);color:var(--text)}
.app{display:flex;flex-direction:column;height:100vh}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:var(--panel);border-bottom:1px solid var(--border)}
.brand{font-weight:600;letter-spacing:.3px}
.brand .dot{color:var(--accent)}
.meta{display:flex;align-items:center;gap:12px}
.pill{font-size:12px;font-weight:700;padding:4px 10px;border-radius:999px}
.pill.pass{background:rgba(46,204,113,.15);color:var(--ok);border:1px solid rgba(46,204,113,.4)}
.pill.fail{background:rgba(255,92,92,.15);color:var(--bad);border:1px solid rgba(255,92,92,.4)}
.ratio{font-size:13px;color:var(--muted)}
.ratio b{color:var(--text)}
.stage{position:relative;flex:1;min-height:0;background:radial-gradient(120% 120% at 50% 0%,#1a2233 0%,#0d111b 70%)}
#view{width:100%;height:100%;display:block;cursor:grab}
#view.panning{cursor:grabbing}
.controls{position:absolute;right:14px;bottom:14px;display:flex;flex-direction:column;gap:8px}
.controls button{width:38px;height:38px;border-radius:10px;border:1px solid var(--border);background:var(--panel-2);color:var(--text);font-size:18px;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.35);transition:transform .05s ease,background .15s}
.controls button:hover{background:#28324a}
.controls button:active{transform:scale(.94)}
.hint{position:absolute;left:14px;bottom:14px;font-size:12px;color:var(--muted);background:rgba(15,20,32,.6);padding:6px 10px;border-radius:8px;border:1px solid var(--border)}
.panel{width:320px;flex:0 0 320px;background:var(--panel);border-left:1px solid var(--border);overflow-y:auto;padding:14px 16px}
.panel section{margin-bottom:18px}
.panel h3{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 8px}
.panel ul{list-style:none;margin:0;padding:0}
.panel li{display:flex;align-items:center;gap:8px;padding:5px 0;font-size:13px;border-bottom:1px solid var(--border)}
.swatch{width:12px;height:12px;border-radius:3px;flex:0 0 auto}
.muted{color:var(--muted);font-weight:400}
#summary,#limitations{font-size:13px;line-height:1.5}
#summary ul,#limitations ul{margin:6px 0 0;padding-left:18px}
</style>
</head>
<body>
<div class="app">
  <header class="topbar">
    <div class="brand"><span class="dot">&#9881;</span> Assembly Viewer</div>
    <div class="meta">
      <span class="pill" id="status">&mdash;</span>
      <span class="ratio">&#28120;&#36895;&#27604; <b id="ratio">&mdash;</b></span>
    </div>
  </header>
  <main class="stage">
    <canvas id="view"></canvas>
    <div class="controls">
      <button id="btn-reset" title="&#35239;&#28857;&#12522;&#12475;&#12483;&#12488;">&#10227;</button>
      <button id="btn-zoom-in" title="&#12470;&#12540;&#12512;&#12452;&#12531;">&#65291;</button>
      <button id="btn-zoom-out" title="&#12470;&#12540;&#12531;&#12450;&#12454;&#12488;">&#65293;</button>
    </div>
    <div class="hint">&#24038;&#12489;&#12521;&#12464;:&#22238;&#36752; &middot; &#21491;&#12489;&#12521;&#12464;:&#31227;&#21205; &middot; &#12507;&#12451;&#12540;&#12523;:&#12470;&#12540;&#12512; &middot; &#28961;&#21046;&#38480;&#22238;&#36752;</div>
  </main>
  <aside class="panel">
    <section><h3>&#27010;&#35201;</h3><div id="summary"></div></section>
    <section><h3>&#37096;&#21697; <span id="part-count" class="muted"></span></h3><ul id="parts"></ul></section>
    <section><h3>&#21046;&#38480;&#20108;&#38918;</h3><div id="limitations"></div></section>
  </aside>
</div>
<script>
const DATA = /*__ASSEMBLY_DATA__*/;
const PARTS = DATA.parts;
const SHAFTS = DATA.shafts;
const canvas = document.getElementById('view');
const ctx = canvas.getContext('2d');
let dpr = window.devicePixelRatio || 1;
let yaw = -0.7, pitch = 0.5, scale = 4, panX = 0, panY = 0;
const LIGHT = (function(){ const v=[0.4,0.7,0.6]; const m=Math.hypot(v[0],v[1],v[2]); return [v[0]/m,v[1]/m,v[2]/m]; })();

function resize(){
  const r = canvas.parentElement.getBoundingClientRect();
  canvas.width = Math.max(1, Math.floor(r.width * dpr));
  canvas.height = Math.max(1, Math.floor(r.height * dpr));
}
window.addEventListener('resize', () => { resize(); draw(); });

function rotate(p){
  const x=p[0], y=p[1], z=p[2];
  const x1 = x*Math.cos(yaw) - z*Math.sin(yaw);
  const z1 = x*Math.sin(yaw) + z*Math.cos(yaw);
  const y2 = y*Math.cos(pitch) - z1*Math.sin(pitch);
  const z2 = y*Math.sin(pitch) + z1*Math.cos(pitch);
  return [x1, y2, z2];
}
function project(p){
  const r = rotate(p);
  return [r[0]*scale + panX, -r[1]*scale + panY, r[2]];
}
function fitView(){
  let minx=1e9,miny=1e9,minz=1e9,maxx=-1e9,maxy=-1e9,maxz=-1e9;
  for(const p of PARTS){ for(const t of p.triangles){ for(const c of t){
    minx=Math.min(minx,c[0]); maxx=Math.max(maxx,c[0]);
    miny=Math.min(miny,c[1]); maxy=Math.max(maxy,c[1]);
    minz=Math.min(minz,c[2]); maxz=Math.max(maxz,c[2]); } } }
  const ext = Math.max(maxx-minx, maxy-miny, (maxz-minz)||1);
  scale = Math.min(canvas.width, canvas.height) / (ext*1.6);
  panX = 0; panY = 0;
}
function shade(tri, base){
  const a=rotate(tri[0]), b=rotate(tri[1]), c=rotate(tri[2]);
  const u=[b[0]-a[0],b[1]-a[1],b[2]-a[2]], w=[c[0]-a[0],c[1]-a[1],c[2]-a[2]];
  let n=[u[1]*w[2]-u[2]*w[1], u[2]*w[0]-u[0]*w[2], u[0]*w[1]-u[1]*w[0]];
  const m=Math.hypot(n[0],n[1],n[2])||1; n=[n[0]/m,n[1]/m,n[2]/m];
  let d=n[0]*LIGHT[0]+n[1]*LIGHT[1]+n[2]*LIGHT[2];
  if(d<0) d=-d;
  const f=0.5+0.5*d;
  const r=parseInt(base.slice(1,3),16), g=parseInt(base.slice(3,5),16), bl=parseInt(base.slice(5,7),16);
  return 'rgb('+Math.round(r*f)+','+Math.round(g*f)+','+Math.round(bl*f)+')';
}
function draw(){
  ctx.setTransform(1,0,0,1,0,0);
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.save();
  ctx.translate(canvas.width/2, canvas.height/2);
  ctx.strokeStyle='rgba(150,160,180,.5)'; ctx.lineWidth=1.5*dpr;
  for(const s of SHAFTS){
    const a=project([s[0],s[1],-50]), b=project([s[0],s[1],120]);
    ctx.beginPath(); ctx.moveTo(a[0],a[1]); ctx.lineTo(b[0],b[1]); ctx.stroke();
  }
  const draws=[];
  for(const p of PARTS){
    for(const tri of p.triangles){
      const pts=tri.map(project);
      const depth=(pts[0][2]+pts[1][2]+pts[2][2])/3;
      draws.push({pts:pts, depth:depth, color:shade(tri,p.color)});
    }
  }
  draws.sort((A,B)=>A.depth-B.depth);
  for(const d of draws){
    ctx.beginPath();
    ctx.moveTo(d.pts[0][0],d.pts[0][1]);
    ctx.lineTo(d.pts[1][0],d.pts[1][1]);
    ctx.lineTo(d.pts[2][0],d.pts[2][1]);
    ctx.closePath();
    ctx.fillStyle=d.color; ctx.fill();
    ctx.strokeStyle='rgba(10,14,22,.35)'; ctx.lineWidth=0.6*dpr; ctx.stroke();
  }
  ctx.fillStyle='#cdd6e6'; ctx.font=(12*dpr)+'px sans-serif';
  for(const p of PARTS){
    const c=project(p.center);
    ctx.fillText(p.id, c[0]+5*dpr, c[1]-4*dpr);
  }
  ctx.restore();
}
let mode=null, lx=0, ly=0;
canvas.addEventListener('contextmenu', e=>e.preventDefault());
canvas.addEventListener('mousedown', e=>{
  mode = (e.button===2 || e.shiftKey) ? 'pan' : 'rotate';
  lx=e.clientX; ly=e.clientY;
  if(mode==='pan') canvas.classList.add('panning');
});
window.addEventListener('mouseup', ()=>{ mode=null; canvas.classList.remove('panning'); });
window.addEventListener('mousemove', e=>{
  if(!mode) return;
  const dx=e.clientX-lx, dy=e.clientY-ly; lx=e.clientX; ly=e.clientY;
  if(mode==='pan'){ panX+=dx*dpr; panY+=dy*dpr; }
  else { yaw+=dx*0.01; pitch+=dy*0.01; }
  draw();
});
canvas.addEventListener('wheel', e=>{
  e.preventDefault();
  scale *= Math.exp(-e.deltaY*0.0015);
  scale = Math.max(0.3, Math.min(12, scale));
  draw();
}, {passive:false});
function zoomBy(f){ scale=Math.max(0.3,Math.min(12,scale*f)); draw(); }
document.getElementById('btn-zoom-in').onclick=()=>zoomBy(1.2);
document.getElementById('btn-zoom-out').onclick=()=>zoomBy(1/1.2);
document.getElementById('btn-reset').onclick=()=>{ yaw=-0.7; pitch=0.5; fitView(); draw(); };

document.getElementById('status').textContent = DATA.status;
document.getElementById('status').className = 'pill ' + DATA.status;
document.getElementById('ratio').textContent = DATA.ratio==null ? '—' : DATA.ratio;
document.getElementById('summary').innerHTML = DATA.summary;
document.getElementById('limitations').innerHTML = DATA.limitations;
document.getElementById('part-count').textContent = '(' + PARTS.length + ')';
const ul=document.getElementById('parts');
for(const p of PARTS){
  const li=document.createElement('li');
  const sw=document.createElement('span'); sw.className='swatch'; sw.style.background=p.color;
  li.appendChild(sw);
  li.appendChild(document.createTextNode(p.id));
  ul.appendChild(li);
}
resize(); fitView(); draw();
</script>
</body>
</html>
"""


def write_assembly_viewer(
    output_path: Path,
    *,
    parts: list[Any],
    report: Any,
    spec: dict[str, Any],
    requirement: dict[str, Any],
    ratio: float | None = None,
) -> dict[str, Any]:
    """Write a self-contained HTML viewer for the assembly and return its artifact record.

    Args:
        output_path: destination ``.html`` path.
        parts: sequence of objects exposing ``part_id``, ``color``, and ``triangles``
            (list of triangles, each a list of three ``[x, y, z]`` vertices already
            placed at the assembly location). Triangles are rendered verbatim, so the
            viewer shows exactly the geometry carried by the STL artifacts.
        report: :class:`cad_agent.assembly_checks.AssemblyCheckReport`.
        spec: Specification JSON (used for limitations / ratio context).
        requirement: Requirement JSON (used for the summary panel).
        ratio: optional speed ratio to display; falls back to
            ``spec["parameter_table"]["total_ratio"]`` when present.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if ratio is None:
        ratio = spec.get("parameter_table", {}).get("total_ratio")

    data = _build_data(parts, report, spec, requirement, ratio)
    html = _HTML_TEMPLATE.replace("__TITLE__", data["title"]).replace(
        "/*__ASSEMBLY_DATA__*/", json.dumps(data, ensure_ascii=False)
    )
    output_path.write_text(html, encoding="utf-8")
    return {
        "artifact_id": f"art_{output_path.stem}",
        "format": "html",
        "path": str(output_path),
        "artifact_hash": _hash_file(output_path),
    }

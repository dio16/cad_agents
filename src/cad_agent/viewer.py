"""Self-contained HTML assembly viewer for human review.

The deterministic surrogate CAD path emits placeholder STEP / box STL, so a human
cannot visually confirm an assembled result from those artifacts alone. This module
generates a single, dependency-free HTML file (no CDN, no network) that renders the
assembly from each part's axis-aligned bounding box using a small Canvas2D 3D
renderer. It is the standard human-review artifact produced by the assembly pipeline
(see :func:`cad_agent.platform_poc.run_assembly_pipeline`).

Known limitation: the viewer shows surrogate bounding boxes, not true part geometry
(e.g. no involute gear teeth). It is a review aid, not a manufacturing drawing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_SHAFT_COLORS = (
    "#4e79a7",
    "#f28e2b",
    "#59a14f",
    "#e15759",
    "#76b7b2",
    "#edc948",
    "#b07aa1",
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


def _build_data(
    parts: list[Any],
    report: Any,
    spec: dict[str, Any],
    requirement: dict[str, Any],
    ratio: float | None,
) -> dict[str, Any]:
    part_data: list[dict[str, Any]] = []
    for index, part in enumerate(parts):
        bbox = part.bbox
        part_data.append(
            {
                "id": part.part_id,
                "color": _SHAFT_COLORS[index % len(_SHAFT_COLORS)],
                "min": [bbox.min_x, bbox.min_y, bbox.min_z],
                "max": [bbox.max_x, bbox.max_y, bbox.max_z],
            }
        )

    centers: set[tuple[float, float]] = set()
    for part in parts:
        bbox = part.bbox
        cx = round((bbox.min_x + bbox.max_x) / 2.0, 3)
        cy = round((bbox.min_y + bbox.max_y) / 2.0, 3)
        centers.add((cx, cy))
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
        + "</ul><p>※ Surrogate CAD は簡易シリンダ/ボックスであり真の歯形は含まれません。真の歯車幾何には新規 DSL 操作の承認が必要です。</p>"
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
  body { margin: 0; font-family: -apple-system, "Segoe UI", sans-serif; color: #1a1a1a; }
  #app { display: flex; height: 100vh; }
  #view { flex: 1 1 auto; background: #f4f6f8; cursor: grab; }
  #view:active { cursor: grabbing; }
  #panel { flex: 0 0 320px; padding: 16px; overflow-y: auto; border-left: 1px solid #ccc; background: #fff; }
  #panel h1 { font-size: 18px; margin: 0 0 12px; }
  #panel h2 { font-size: 14px; margin: 16px 0 6px; border-bottom: 1px solid #eee; padding-bottom: 4px; }
  #status.pass { color: #1a7f37; font-weight: bold; }
  #status.fail { color: #cf222e; font-weight: bold; }
  .hint { color: #666; font-size: 12px; margin-top: 16px; }
  ul { margin: 0; padding-left: 18px; }
  li { margin: 2px 0; }
</style>
</head>
<body>
<div id="app">
  <canvas id="view" width="800" height="600"></canvas>
  <div id="panel">
    <h1 id="title"></h1>
    <p>ステータス: <span id="status"></span></p>
    <p>減速比: <span id="ratio"></span></p>
    <h2>概要</h2><div id="summary"></div>
    <h2>部品</h2><ul id="parts"></ul>
    <h2>制限事項</h2><div id="limitations"></div>
    <p class="hint">マウスドラッグで回転 / ホイールでズーム。並列軸は灰色の線で表示。</p>
  </div>
</div>
<script>
const DATA = /*__ASSEMBLY_DATA__*/;
const PARTS = DATA.parts;
const SHAFTS = DATA.shafts;
const canvas = document.getElementById('view');
const ctx = canvas.getContext('2d');
let yaw = -0.7, pitch = 0.5, dist = 620;

function project(p) {
  let x = p[0], y = p[1], z = p[2];
  let x1 = x * Math.cos(yaw) - z * Math.sin(yaw);
  let z1 = x * Math.sin(yaw) + z * Math.cos(yaw);
  let y2 = y * Math.cos(pitch) - z1 * Math.sin(pitch);
  let z2 = y * Math.sin(pitch) + z1 * Math.cos(pitch);
  let f = dist / (dist + z2);
  return [x1 * f, -y2 * f, z2];
}

function boxFaces(min, max) {
  const [x0, y0, z0] = min, [x1, y1, z1] = max;
  const v = [
    [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
    [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]
  ];
  return [
    [v[0], v[1], v[2], v[3]],
    [v[4], v[5], v[6], v[7]],
    [v[0], v[1], v[5], v[4]],
    [v[3], v[2], v[6], v[7]],
    [v[0], v[3], v[7], v[4]],
    [v[1], v[2], v[6], v[5]]
  ];
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.strokeStyle = '#9aa0a6';
  ctx.lineWidth = 1;
  for (const s of SHAFTS) {
    const a = project([s[0], s[1], -40]);
    const b = project([s[0], s[1], 110]);
    ctx.beginPath();
    ctx.moveTo(a[0], a[1]);
    ctx.lineTo(b[0], b[1]);
    ctx.stroke();
  }
  const draws = [];
  for (const p of PARTS) {
    const faces = boxFaces(p.min, p.max);
    for (const f of faces) {
      const pts = f.map(project);
      const depth = (pts[0][2] + pts[1][2] + pts[2][2] + pts[3][2]) / 4;
      draws.push({ pts: pts, depth: depth, color: p.color, id: p.id });
    }
  }
  draws.sort((A, B) => A.depth - B.depth);
  for (const d of draws) {
    ctx.beginPath();
    ctx.moveTo(d.pts[0][0], d.pts[0][1]);
    for (let i = 1; i < d.pts.length; i++) ctx.lineTo(d.pts[i][0], d.pts[i][1]);
    ctx.closePath();
    ctx.globalAlpha = 0.85;
    ctx.fillStyle = d.color;
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.strokeStyle = '#222';
    ctx.lineWidth = 1;
    ctx.stroke();
  }
  ctx.fillStyle = '#111';
  ctx.font = '12px sans-serif';
  for (const p of PARTS) {
    const c = project([(p.min[0] + p.max[0]) / 2, (p.min[1] + p.max[1]) / 2, (p.min[2] + p.max[2]) / 2]);
    ctx.fillText(p.id, c[0] + 5, c[1] - 4);
  }
  ctx.restore();
}

let drag = false, lx = 0, ly = 0;
canvas.addEventListener('mousedown', (e) => { drag = true; lx = e.clientX; ly = e.clientY; });
window.addEventListener('mouseup', () => { drag = false; });
window.addEventListener('mousemove', (e) => {
  if (!drag) return;
  yaw += (e.clientX - lx) * 0.01;
  pitch += (e.clientY - ly) * 0.01;
  lx = e.clientX; ly = e.clientY;
  draw();
});
canvas.addEventListener('wheel', (e) => {
  dist += e.deltaY * 0.5;
  dist = Math.max(200, dist);
  e.preventDefault();
  draw();
}, { passive: false });

document.getElementById('title').textContent = DATA.title;
document.getElementById('status').textContent = DATA.status;
document.getElementById('status').className = DATA.status;
document.getElementById('ratio').textContent = DATA.ratio;
document.getElementById('summary').innerHTML = DATA.summary;
document.getElementById('limitations').innerHTML = DATA.limitations;
const ul = document.getElementById('parts');
for (const p of PARTS) {
  const li = document.createElement('li');
  li.textContent = p.id + ' (' + p.color + ')';
  ul.appendChild(li);
}
draw();
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
        parts: sequence of :class:`cad_agent.assembly_checks.AssemblyPart`.
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

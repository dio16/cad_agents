from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from PIL import ImageChops
from playwright.sync_api import sync_playwright
from v27_evidence import evidence_fields, sha256


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v27_connected_package"
VIEWER = PACKAGE / "v27_3d_cad_motion_viewer.html"
OUT = PACKAGE / "v27_wsl_http_viewer_smoke.json"
SHOT = PACKAGE / "v27_wsl_http_viewer_smoke.png"
SHOT_LATER = PACKAGE / "v27_wsl_http_viewer_smoke_later.png"
USER_LIB = Path("/home/diobrando/codex_wsl/browser_deps/root/usr/lib/x86_64-linux-gnu")


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def non_background_ratio(path: Path) -> float:
    img = Image.open(path).convert("RGB")
    bg = (16, 24, 32)
    changed = 0
    total = img.width * img.height
    for r, g, b in img.getdata():
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 35:
            changed += 1
    return changed / total


def image_difference_ratio(a: Path, b: Path) -> float:
    diff = ImageChops.difference(Image.open(a).convert("RGB"), Image.open(b).convert("RGB"))
    extrema = diff.getbbox()
    if extrema is None:
        return 0.0
    changed = 0
    total = diff.width * diff.height
    for r, g, b in diff.getdata():
        if r + g + b > 18:
            changed += 1
    return changed / total


def main() -> int:
    port = free_port()
    server = subprocess.Popen(
        ["python3", "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=PACKAGE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/{VIEWER.name}"
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        **evidence_fields(),
        "status": "fail",
        "source_viewer": str(VIEWER),
        "viewer_sha256": sha256(VIEWER),
        "url": url,
        "screenshot": str(SHOT),
        "checks": [],
    }
    console_messages: list[str] = []
    page_errors: list[str] = []
    try:
        time.sleep(0.5)
        with sync_playwright() as p:
            env = os.environ.copy()
            if USER_LIB.exists():
                env["LD_LIBRARY_PATH"] = f"{USER_LIB}:{env.get('LD_LIBRARY_PATH', '')}"
            browser = p.chromium.launch(headless=True, args=["--use-gl=swiftshader", "--ignore-gpu-blocklist"], env=env)
            page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
            page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            response = page.goto(url, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1800)
            status_text = page.locator("#status").inner_text()
            ratio_text_initial = page.locator("#ratioReadout").inner_text()
            canvas_count = page.locator("canvas").count()
            page.screenshot(path=str(SHOT), full_page=False)
            state_before = page.evaluate("window.__v27Debug.getState()")
            page.wait_for_timeout(900)
            ratio_text_later = page.locator("#ratioReadout").inner_text()
            state_later = page.evaluate("window.__v27Debug.getState()")
            page.screenshot(path=str(SHOT_LATER), full_page=False)
            page.locator("#pose").fill("90")
            page.locator("#pose").dispatch_event("input")
            page.wait_for_timeout(120)
            state_pose_90 = page.evaluate("window.__v27Debug.getState()")
            page.mouse.move(380, 420)
            page.mouse.down()
            page.mouse.move(500, 360)
            page.mouse.up()
            page.wait_for_timeout(120)
            state_after_drag = page.evaluate("window.__v27Debug.getState()")
            browser.close()
        ratio = non_background_ratio(SHOT)
        frame_delta = image_difference_ratio(SHOT, SHOT_LATER)
        failed_console = [item for item in console_messages if item.startswith(("error:", "assert:"))]
        checks = [
            {"name": "HTTP response OK", "status": "pass" if response and response.ok else "fail"},
            {"name": "viewer creates WebGL canvas", "status": "pass" if canvas_count >= 1 else "fail", "canvas_count": canvas_count},
            {"name": "viewer loaded V27 actual CAD meshes", "status": "pass" if "Loaded V27 9 CAD mesh parts" in status_text else "fail", "status_text": status_text},
            {"name": "viewer ratio readout names pin-slot display", "status": "pass" if "pin-slot pallet display" in ratio_text_initial else "fail", "ratio_text": ratio_text_initial},
            {"name": "viewer advances while playing", "status": "pass" if state_later["thetaDeg"] > state_before["thetaDeg"] and ratio_text_later != ratio_text_initial else "fail", "before": state_before, "later": state_later},
            {"name": "viewer render changes between frames", "status": "pass" if frame_delta > 0.002 else "fail", "frame_difference_ratio": round(frame_delta, 4)},
            {"name": "pose control moves to requested angle", "status": "pass" if abs(state_pose_90["thetaDeg"] - 90.0) < 0.2 else "fail", "state": state_pose_90},
            {"name": "camera drag changes view", "status": "pass" if state_after_drag["yaw"] != state_pose_90["yaw"] or state_after_drag["pitch"] != state_pose_90["pitch"] else "fail", "before": state_pose_90, "after": state_after_drag},
            {"name": "screenshot has non-background pixels", "status": "pass" if ratio > 0.08 else "fail", "non_background_ratio": round(ratio, 4)},
            {"name": "browser console has no errors", "status": "pass" if not failed_console and not page_errors else "fail", "console_errors": failed_console, "page_errors": page_errors},
        ]
        result["checks"] = checks
        result["status"] = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    except Exception as exc:
        result["checks"] = [{"name": "V27 WSL HTTP viewer smoke executed", "status": "fail", "error": f"{type(exc).__name__}: {exc}"}]
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(OUT), "screenshot": str(SHOT)}, indent=2))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

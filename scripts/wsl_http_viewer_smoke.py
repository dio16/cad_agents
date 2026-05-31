from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v26_mechanical_package"
VIEWER = PACKAGE / "v26_3d_cad_motion_viewer.html"
OUT = PACKAGE / "wsl_http_viewer_smoke.json"
SHOT = PACKAGE / "wsl_http_viewer_smoke.png"
USER_LIB = Path("/home/diobrando/codex_wsl/browser_deps/root/usr/lib/x86_64-linux-gnu")


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def non_background_ratio(path: Path) -> float:
    img = Image.open(path).convert("RGB")
    width, height = img.size
    bg = (16, 24, 32)
    changed = 0
    total = width * height
    for r, g, b in img.getdata():
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 35:
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
    console_messages: list[str] = []
    page_errors: list[str] = []
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "fail",
        "url": url,
        "screenshot": str(SHOT),
        "checks": [],
    }
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
            page.wait_for_timeout(2500)
            canvas_count = page.locator("canvas").count()
            status_text = page.locator("#status").inner_text(timeout=3000) if page.locator("#status").count() else ""
            ratio_text = page.locator("#ratioReadout").inner_text(timeout=3000) if page.locator("#ratioReadout").count() else ""
            page.screenshot(path=str(SHOT), full_page=False)
            browser.close()
        ratio = non_background_ratio(SHOT)
        failed_console = [item for item in console_messages if item.startswith(("error:", "assert:"))]
        checks = [
            {"name": "HTTP response OK", "status": "pass" if response and response.ok else "fail", "status_code": response.status if response else None},
            {"name": "viewer creates WebGL canvas", "status": "pass" if canvas_count >= 1 else "fail", "canvas_count": canvas_count},
            {"name": "viewer loaded mesh status text", "status": "pass" if "Loaded 9 CAD mesh parts" in status_text else "fail", "status_text": status_text},
            {"name": "viewer ratio readout populated", "status": "pass" if "orbit relative -4" in ratio_text else "fail", "ratio_text": ratio_text},
            {"name": "screenshot has non-background pixels", "status": "pass" if ratio > 0.08 else "fail", "non_background_ratio": round(ratio, 4)},
            {"name": "browser console has no errors", "status": "pass" if not failed_console and not page_errors else "fail", "console_errors": failed_console, "page_errors": page_errors},
        ]
        result["checks"] = checks
        result["status"] = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    except Exception as exc:
        result["checks"] = [
            {
                "name": "WSL HTTP browser smoke executed",
                "status": "fail",
                "error": f"{type(exc).__name__}: {exc}",
            }
        ]
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

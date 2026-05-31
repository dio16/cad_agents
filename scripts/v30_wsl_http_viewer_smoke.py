from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v30_mechanical_sculpture_package"
SUMMARY = PACKAGE / "v30_package_summary.json"
VIEWER = PACKAGE / "v30_3d_cad_motion_viewer.html"
OUT = PACKAGE / "v30_wsl_http_viewer_smoke.json"
SHOT = PACKAGE / "v30_wsl_http_viewer_smoke.png"
USER_LIB = Path("/home/diobrando/codex_wsl/browser_deps/root/usr/lib/x86_64-linux-gnu")


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main() -> int:
    port = free_port()
    server = subprocess.Popen(
        ["python3", "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=PACKAGE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/{VIEWER.name}"
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    result = {"created_at": datetime.now(timezone.utc).isoformat(), "generation_id": summary.get("generation_id"), "status": "fail", "url": url, "checks": []}
    try:
        time.sleep(0.5)
        with sync_playwright() as p:
            env = os.environ.copy()
            if USER_LIB.exists():
                env["LD_LIBRARY_PATH"] = f"{USER_LIB}:{env.get('LD_LIBRARY_PATH', '')}"
            browser = p.chromium.launch(headless=True, args=["--use-gl=swiftshader", "--ignore-gpu-blocklist"], env=env)
            page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
            response = page.goto(url, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1200)
            status_text = page.locator("#status").inner_text()
            ratio_initial = page.locator("#ratioReadout").inner_text()
            page.wait_for_timeout(700)
            ratio_later = page.locator("#ratioReadout").inner_text()
            claim_note = page.locator("#claimNote").inner_text()
            page.screenshot(path=str(SHOT), full_page=False)
            browser.close()
        checks = [
            {"name": "HTTP response OK", "status": "pass" if response and response.ok else "fail"},
            {"name": "viewer loaded solids", "status": "pass" if "Loaded V30 18 CAD mesh solids" in status_text else "fail", "status_text": status_text},
            {"name": "viewer advances over time", "status": "pass" if ratio_initial != ratio_later else "fail"},
            {"name": "viewer wording names real shafts", "status": "pass" if "real shafts" in claim_note else "fail"},
        ]
        result["checks"] = checks
        result["status"] = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    except Exception as exc:
        result["checks"] = [{"name": "viewer smoke executed", "status": "fail", "error": f"{type(exc).__name__}: {exc}"}]
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

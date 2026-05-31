from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import colorsys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from v27_evidence import evidence_fields


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reports" / "fabrication_v27_connected_package"
VIEWER = PACKAGE / "v27_3d_cad_motion_viewer.html"
OUT = PACKAGE / "v27_visibility_audit.json"
SHEET = PACKAGE / "v27_visibility_contact_sheet.png"
USER_LIB = Path("/home/diobrando/codex_wsl/browser_deps/root/usr/lib/x86_64-linux-gnu")
SAMPLES = [0, 90, 180, 270]
ROLE_HUE_RANGES = {
    "carrier": [(35, 65)],
    "orbit_escape_pinion": [(10, 32)],
    "hand_input_pinion": [(290, 325)],
    "balance_wheel": [(90, 150)],
    "escape_wheel": [(330, 360), (0, 12)],
    "pallet_display": [(180, 220)],
}


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def color_counts(path: Path) -> dict[str, int]:
    img = Image.open(path).convert("RGB")
    counts = {role: 0 for role in ROLE_HUE_RANGES}
    for r, g, b in img.crop((0, 0, min(940, img.width), img.height)).getdata():
        hue, saturation, value = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        hue *= 360.0
        if saturation < 0.45 or value < 0.18:
            continue
        for role, ranges in ROLE_HUE_RANGES.items():
            if any(low <= hue <= high for low, high in ranges):
                counts[role] += 1
    return counts


def contact_sheet(paths: list[tuple[int, Path]]) -> None:
    tiles = []
    for angle, path in paths:
        img = Image.open(path).convert("RGB")
        tile = img.crop((0, 0, min(940, img.width), img.height)).resize((470, 450))
        draw = ImageDraw.Draw(tile)
        draw.rectangle((0, 0, 118, 28), fill=(16, 24, 32))
        draw.text((10, 7), f"{angle} deg", fill=(238, 243, 246))
        tiles.append(tile)
    sheet = Image.new("RGB", (940, 900), (16, 24, 32))
    for idx, tile in enumerate(tiles):
        sheet.paste(tile, ((idx % 2) * 470, (idx // 2) * 450))
    sheet.save(SHEET)


def main() -> int:
    port = free_port()
    server = subprocess.Popen(
        ["python3", "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=PACKAGE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    captures: list[tuple[int, Path]] = []
    checks: list[dict] = []
    role_min_counts = {role: None for role in ROLE_HUE_RANGES}
    try:
        time.sleep(0.5)
        with sync_playwright() as p:
            env = os.environ.copy()
            if USER_LIB.exists():
                env["LD_LIBRARY_PATH"] = f"{USER_LIB}:{env.get('LD_LIBRARY_PATH', '')}"
            browser = p.chromium.launch(headless=True, args=["--use-gl=swiftshader", "--ignore-gpu-blocklist"], env=env)
            page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
            page.goto(f"http://127.0.0.1:{port}/{VIEWER.name}", wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1200)
            page.evaluate("window.__v27Debug.pause()")
            page.evaluate("window.__v27Debug.setReviewMode(true)")
            page.evaluate("window.__v27Debug.setView('top')")
            for angle in SAMPLES:
                shot = PACKAGE / f"v27_visibility_{angle:03d}.png"
                page.evaluate("(angle) => window.__v27Debug.setPoseDeg(angle)", angle)
                page.wait_for_timeout(120)
                page.screenshot(path=str(shot), full_page=False)
                captures.append((angle, shot))
                counts = color_counts(shot)
                for role, count in counts.items():
                    role_min_counts[role] = count if role_min_counts[role] is None else min(role_min_counts[role], count)
            browser.close()
        contact_sheet(captures)
        for role, count in role_min_counts.items():
            checks.append(
                {
                    "name": f"{role} remains visibly rendered across sampled poses",
                    "status": "pass" if count is not None and count >= 24 else "fail",
                    "min_detected_pixels": count,
                }
            )
    except Exception as exc:
        checks = [{"name": "visibility audit executed", "status": "fail", "error": f"{type(exc).__name__}: {exc}"}]
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    status = "pass" if checks and all(check["status"] == "pass" for check in checks) else "fail"
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        **evidence_fields(),
        "status": status,
        "sample_angles_deg": SAMPLES,
        "detector": {
            "mode": "viewer_review_mode_hue_detection",
            "review_mode_enabled": True,
            "role_hue_ranges_deg": ROLE_HUE_RANGES,
        },
        "contact_sheet": str(SHEET),
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(OUT), "contact_sheet": str(SHEET)}, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

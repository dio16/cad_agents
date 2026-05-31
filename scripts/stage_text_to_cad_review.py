from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "manifests" / "tourbillon_v20.json"
DEFAULT_EXTERNAL = REPO_ROOT.parents[0] / "external" / "text-to-cad"
DEFAULT_OUT = REPO_ROOT / "reports" / "text_to_cad_review" / "tourbillon_v20"


def _wsl_to_windows(path_text: str) -> Path:
    if path_text.startswith("/home/"):
        if os.name != "nt":
            return Path(path_text)
        return Path(r"\\wsl.localhost\Ubuntu-24.04") / path_text.lstrip("/")
    return Path(path_text)


def _wsl_path(path: Path) -> str:
    text = str(path)
    if text.startswith(r"\\wsl.localhost\Ubuntu-24.04"):
        return text.replace(r"\\wsl.localhost\Ubuntu-24.04", "").replace("\\", "/")
    if len(text) > 2 and text[1] == ":":
        drive = text[0].lower()
        rest = text[2:].replace("\\", "/")
        return f"/mnt/{drive}{rest}"
    return text.replace("\\", "/")


def _copy_step(src_text: str, dest_dir: Path) -> dict:
    src = _wsl_to_windows(src_text)
    if not src.exists():
        raise FileNotFoundError(f"Missing STEP source: {src_text} -> {src}")
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return {
        "source": src_text,
        "staged": str(dest),
        "staged_wsl": _wsl_path(dest),
        "size_bytes": dest.stat().st_size,
    }


def _run_text_to_cad(targets: list[Path], external: Path, summary: bool) -> list[dict]:
    scripts_dir = external / "skills" / "cad" / "scripts"
    command_results = []
    for target in targets:
        command = [
            sys.executable,
            "-m",
            "gen_step_part",
            _wsl_path(target),
        ]
        if summary:
            command.append("--summary")
        completed = subprocess.run(
            command,
            cwd=_wsl_path(scripts_dir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        command_results.append(
            {
                "target": str(target),
                "command": command,
                "returncode": completed.returncode,
                "output_tail": completed.stdout[-4000:],
            }
        )
    return command_results


def _text_to_cad_glb_path(step_path: Path) -> Path:
    return step_path.parent / f".{step_path.name}" / "model.glb"


def stage_review(
    manifest_path: Path,
    output_dir: Path,
    external: Path,
    run_text_to_cad: bool,
    summary: bool,
) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    step_dir = output_dir / "step"
    step_dir.mkdir(parents=True, exist_ok=True)

    staged_parts = []
    for item in manifest.get("parts", []):
        copied = _copy_step(item["file"], step_dir)
        copied.update({"name": item.get("name"), "role": item.get("role"), "kind": "mechanism_part"})
        staged_parts.append(copied)
    for item in manifest.get("standard_hardware_files", []):
        copied = _copy_step(item["file"], step_dir)
        copied.update({"name": item.get("name"), "role": item.get("role"), "kind": "standard_hardware"})
        staged_parts.append(copied)

    motion_preview = manifest.get("motion_preview", {}).get("file")
    copied_motion = None
    if motion_preview:
        motion_src = REPO_ROOT / motion_preview
        if motion_src.exists():
            motion_dest = output_dir / motion_src.name
            shutil.copy2(motion_src, motion_dest)
            copied_motion = str(motion_dest)

    command_results: list[dict] = []
    if run_text_to_cad:
        command_results = _run_text_to_cad([Path(item["staged"]) for item in staged_parts], external, summary)

    review_manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(manifest_path),
        "source_document_url": manifest.get("document_url"),
        "status": "pass" if all(r.get("returncode", 0) == 0 for r in command_results) else "warning",
        "text_to_cad_root": str(external),
        "text_to_cad_scripts_wsl": _wsl_path(external / "skills" / "cad" / "scripts"),
        "staged_parts": staged_parts,
        "motion_preview": copied_motion,
        "commands": {
            "generate_sidecars_for_one_step": (
                "cd '{scripts}' && python -m gen_step_part '{step}' --summary"
            ).format(
                scripts=_wsl_path(external / "skills" / "cad" / "scripts"),
                step=staged_parts[0]["staged_wsl"] if staged_parts else "",
            ),
            "snapshot_example": (
                "cd '{scripts}' && python -m snapshot '{glb}' --views isometric,top "
                "--out-dir '{out}'"
            ).format(
                scripts=_wsl_path(external / "skills" / "cad" / "scripts"),
                glb=_wsl_path(_text_to_cad_glb_path(Path(staged_parts[0]["staged"]))) if staged_parts else "",
                out=_wsl_path(output_dir / "snapshots"),
            ),
        },
        "text_to_cad_results": command_results,
    }
    (output_dir / "review_manifest.json").write_text(
        json.dumps(review_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    readme = [
        "# Tourbillon V20 text-to-CAD Review Staging",
        "",
        "This directory stages the current V20 STEP outputs for optional text-to-CAD sidecar, cadref, and snapshot review.",
        "",
        "Source of truth remains the CadQuery generator and `manifests/tourbillon_v20.json`; do not edit staged STEP files.",
        "",
        "Useful commands:",
        "",
        f"- Sidecar summary: `{review_manifest['commands']['generate_sidecars_for_one_step']}`",
        f"- Snapshot example: `{review_manifest['commands']['snapshot_example']}`",
        "",
        "The primary mechanical gates remain design checks, geometry selector audit, motion preview, Onshape pose snapshots, and solid interference audit.",
    ]
    (output_dir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    return review_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage tourbillon STEP outputs for text-to-CAD review.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--text-to-cad-root", type=Path, default=DEFAULT_EXTERNAL)
    parser.add_argument("--run-text-to-cad", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    result = stage_review(
        manifest_path=args.manifest,
        output_dir=args.out_dir,
        external=args.text_to_cad_root,
        run_text_to_cad=args.run_text_to_cad,
        summary=args.summary,
    )
    print(json.dumps({"status": result["status"], "out_dir": str(args.out_dir)}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

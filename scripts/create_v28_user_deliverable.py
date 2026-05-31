from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports" / "fabrication_v28_mechanism_package"
SOURCE_MANIFEST = ROOT / "manifests" / "tourbillon_v28_mechanism_contract.json"
OUT = ROOT / "deliverables" / "tourbillon_v28"
ZIP_NAME = "tourbillon_v28_print_bundle.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_tree(src: Path, dst: Path) -> list[str]:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return [str(path.relative_to(OUT)) for path in sorted(dst.rglob("*")) if path.is_file()]


def rewrite_csv(src: Path, dst: Path) -> None:
    with src.open(newline="", encoding="utf-8") as in_fh, dst.open("w", newline="", encoding="utf-8") as out_fh:
        reader = csv.reader(in_fh)
        writer = csv.writer(out_fh)
        for row in reader:
            writer.writerow([cell.replace(str(SOURCE), ".") for cell in row])


def write_readmes() -> None:
    en = """# Tourbillon V28 user deliverable

This folder is the direct handoff package for the mechanically driven tabletop tourbillon mechanism.

## Start here

- Printable parts: `stl/`
- Motion viewer: `viewer.html`
- Quick previews: `preview.png`, `preview_contact_sheet.png`
- Printable-part guidance: `printed_parts.csv`
- Purchased parts: `purchased_parts.csv`
- Assembly order: `assembly_sequence.csv`
- Portable archive: `tourbillon_v28_print_bundle.zip`

## Scope

This is a locally validated fabrication package for a mechanically driven tabletop mechanism with a non-regulating demonstrative escapement. Native Onshape verification and physical print results are not claimed here.
"""
    ja = """# Tourbillon V28 ユーザー向け成果物

このフォルダが、機械推進器付きトゥールビオン機構の卓上オブジェを直接受け取るための成果物です。

## まず使うもの

- 印刷用 STL: `stl/`
- 動作確認ビューアー: `viewer.html`
- 事前確認画像: `preview.png`, `preview_contact_sheet.png`
- 印刷部品ガイド: `printed_parts.csv`
- 購入部品: `purchased_parts.csv`
- 組立順: `assembly_sequence.csv`
- まとめて渡す zip: `tourbillon_v28_print_bundle.zip`

## 主張範囲

これは、非調速のデモ用脱進機を備えた機械駆動卓上機構について、ローカル検証済みの fabrication package です。Native Onshape 検証と物理プリント結果はまだ主張しません。
"""
    (OUT / "README.md").write_text(en, encoding="utf-8")
    (OUT / "README_JA.md").write_text(ja, encoding="utf-8")

    current_index = """# Current deliverable

Latest user-facing package: `tourbillon_v28/`

- Printable STL files: `tourbillon_v28/stl/`
- Motion viewer: `tourbillon_v28/viewer.html`
- Preview: `tourbillon_v28/preview.png`
- Portable archive: `tourbillon_v28/tourbillon_v28_print_bundle.zip`
"""
    current_index_ja = """# 現在の成果物

最新のユーザー向け成果物: `tourbillon_v28/`

- 印刷用 STL: `tourbillon_v28/stl/`
- 動作確認ビューアー: `tourbillon_v28/viewer.html`
- 事前確認画像: `tourbillon_v28/preview.png`
- まとめ zip: `tourbillon_v28/tourbillon_v28_print_bundle.zip`
"""
    (OUT.parent / "README.md").write_text(current_index, encoding="utf-8")
    (OUT.parent / "README_JA.md").write_text(current_index_ja, encoding="utf-8")


def main() -> int:
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    copied.extend(copy_tree(SOURCE / "stl", OUT / "stl"))
    copied.extend(copy_tree(SOURCE / "step", OUT / "step"))
    shutil.copy2(SOURCE / "v28_3d_cad_motion_viewer.html", OUT / "viewer.html")
    shutil.copy2(SOURCE / "v28_wsl_http_viewer_smoke.png", OUT / "preview.png")
    shutil.copy2(SOURCE / "v28_visibility_contact_sheet.png", OUT / "preview_contact_sheet.png")
    copied.extend(["viewer.html", "preview.png", "preview_contact_sheet.png"])
    for name in ("printed_parts.csv", "purchased_parts.csv", "assembly_sequence.csv"):
        rewrite_csv(SOURCE / name, OUT / name)
        copied.append(name)
    write_readmes()
    copied.extend(["README.md", "README_JA.md"])

    files = []
    for rel in sorted(set(copied)):
        path = OUT / rel
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_package": "reports/fabrication_v28_mechanism_package",
        "source_manifest": "manifests/tourbillon_v28_mechanism_contract.json",
        "generation_id": source_manifest["generation_id"],
        "object_class": "mechanically-driven-tabletop-mechanism",
        "viewer_entrypoint": "viewer.html",
        "printable_parts_dir": "stl",
        "preview_files": ["preview.png", "preview_contact_sheet.png"],
        "bom_files": ["printed_parts.csv", "purchased_parts.csv"],
        "assembly_file": "assembly_sequence.csv",
        "files": files,
    }
    (OUT / "package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    current_delivery = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generation_id": source_manifest["generation_id"],
        "package_path": "deliverables/tourbillon_v28",
        "viewer_entrypoint": "deliverables/tourbillon_v28/viewer.html",
        "printable_parts_dir": "deliverables/tourbillon_v28/stl",
        "human_index": "deliverables/README.md",
        "human_index_ja": "deliverables/README_JA.md",
    }
    (OUT.parent / "current_delivery.json").write_text(json.dumps(current_delivery, indent=2), encoding="utf-8")

    with zipfile.ZipFile(OUT / ZIP_NAME, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.rglob("*")):
            if path.is_file() and path.name != ZIP_NAME:
                archive.write(path, path.relative_to(OUT))

    print(json.dumps({"status": "pass", "deliverable_dir": str(OUT), "zip": str(OUT / ZIP_NAME)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

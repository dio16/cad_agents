# CAD-FG-14 Implementation Plan — HTML Assembly Viewer (Standard Output) + 7-Stage Workflow Embedding

## Goal
- Assy (組立) 結果を人が目視確認できるよう、組立に対して標準で HTML ビューアーを出力する機能改善を行う。
- 全体設計フロー（構想 → 詳細設計 → 設計案review → 案の敵対的review → 実装計画作成 → 実装 → テストケースでテスト）に組み込む。

## Classification
- `executable_now`

## Deliverables
1. `src/cad_agent/viewer.py` — `write_assembly_viewer()`: 自己完結型 HTML（外部 CDN / ネットワーク非依存）の Canvas2D 3D 三角メッシュレンダラ。各ギアの実 STL メッシュをアセンブリ位置に配置して描画。
2. `src/cad_agent/platform_poc.py` — `run_assembly_pipeline()`: ギアごとに surrogate CAD を実行し AABB で組立、標準で HTML ビューアーを出力。
3. `examples/gear_train_v1/run_test.py` — パイプライン利用に書き換え、`assembly_viewer.html` を artifacts（成果物と同じ場所）へ出力。
4. ドキュメント: `ORCHESTRATOR_WORKFLOW.md` (7-stage flow), `cad_agent_detailed_design.md` (§16), `operations_ja.md` (HTML ビューアー節)。
5. `tests/test_viewer.py` — viewer + pipeline のテスト。

## Constraints / decisions
- Mechanism DSL allowlist (box / cylinder / through_hole + shaft) は維持。`gear` は未承認（真の歯形は新規 DSL 操作の承認必要）。
- 新しい Workflow 状態は追加しない（FG-12 regression 回避）。
- 循環 import 回避のため `viewer.py` は `platform_poc` を import しない（呼び出し側 `run_assembly_pipeline` が局所 import で `viewer` を参照）。
- ビューアーは run_cad_runtime が出力した実 STL メッシュ（binary/ASCII を自動判定して解析）をアセンブリ位置に配置して描画する。Surrogate 環境では STL が簡易ボックスメッシュとなるため、表示もそれに従う。STEP はメタデータ placeholder のため可視化には STL を用いる。

## Validation
- `uv run pytest -q` (targets: tests/test_viewer.py) → pass
- `bash ./run_cad_agent.sh validate-docs` → pass
- `bash ./run_cad_agent.sh status` → aligned
- `git diff --check` → clean
- `uv run python examples/gear_train_v1/run_test.py` → exit 0, viewer emitted

## Deviation record
- None.
## Refinements (post initial implementation)
- **Refinement A** (`692b91b`): ビューアー HTML を成果物と同じ artifacts ディレクトリへ出力。
- **Refinement B** (`00ff1d4`): 表示ジオメトリを runtime `bbox_mm` に合わせ、pan + モダン UI を追加。
- **Refinement C** (2026-07-12): 以下の2点を修正。
  - 無制限回転: ピッチ角のクランプ（`[-1.5,1.5]`）を解除し、裏側まで回転可視化可能に。
  - 実幾何との一致: surrogate の AABB ボックスではなく、`run_cad_runtime` が出力した STL の三角面をそのまま描画。 viewer は `read_stl_triangles()` で binary/ASCII STL を解析し、`run_assembly_pipeline` が各パーツをアセンブリ位置へ平行移動して配置。これによりビューアー表示と STEP/STL 成果物が一致。

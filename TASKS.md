# Tasks

> **完了済みタスクの詳細**: `docs/backlog/IMPLEMENTATION_HISTORY.md`
> **詳細実装計画**: `docs/cadagent_plans/<TASK_ID>/implementation-plan.md`
> **高位の実装計画**: `docs/cad_agent_implementation_plan.md`

## 現在の成熟度

- PoC/Pilot 全フェーズ (CAD-P00–P09) 実装・検証済み
- Functional gap (CAD-FG-00–FG-22) 全タスク完了
- CAD-REVIEW-01/02 キャッチアップバッチ完了
- 最終検証: `uv run pytest -q` → 288 passed, 2 subtests; `validate-docs` pass
- 延期: Production v1/v2 本番デプロイ (Kubernetes, Cosign, real worker pools, FEA, 本番認証)

## アクティブタスク

_現在アクティブな実装タスクはありません。_

## 保留/承認待ち

| Task | 内容 | 分類 |
|---|---|---|
| _(none)_ | — | — |

## 延期 (deferred)

- Kubernetes / KServe / Argo CD / Cosign / Trivy 本番運用
- 実 sandbox CAD worker pool (OCCT/FreeCAD/Blender native)
- 実材料 DB / PLM/ERP/MES 連携 / テナント分離
- FEA / 本番 motion sweep / 接触解析
- 本格認証 (OIDC) / マルチテナント
- Production SLO  enforcement
- 新規 DSL operation (allowlist 拡張は人間承認ゲート)

## タスク実行ルール

1. `prompt.md` が本ファイルを読み込み、タスクを分類する
2. `executable_now` → 即実行。`approval_required` → ユーザー承認待ち
3. 詳細計画パスは本ファイルが制御する（現在の既定: `docs/cadagent_plans/<TASK_ID>/implementation-plan.md`）
4. タスク完了時は検証 evidence を記録し、本ファイルを更新する

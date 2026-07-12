# CAD-REVIEW-01 — Code Review改善 実装計画

> **Boundary:** This is the master implementation plan for all review-based improvement tasks. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** `docs/cad_agent_detailed_design.md` と実装の差分レビューで特定された問題を修正し、設計仕様との整合性を改善する。

**Architecture:** 各レビュー指摘を独立したCAD-FG-*タスクに分解し、既存のprompt-driven workflowに従って段階的に実装する。全タスクは既存の210テストを回帰させながら進める。

**Tech Stack:** Python 3.11+, CadQuery (optional), pytest, JSON Schema, stdlib http.server.

## Execution Workflow: superpowers:subagent-driven-development

本計画は `superpowers:subagent-driven-development` skill に従って実行する。

### Skill Integration

| スキル | 適用タイミング | 用途 |
|---|---|---|
| `superpowers:subagent-driven-development` | 全フェーズ実行 | タスク分散 + 自動レビュー (implementer + task-reviewer) |
| `superpowers:test-driven-development` | 各 subagent 内 | RED→GREEN→REFACTOR の厳格な適用 |
| `superpowers:dispatching-parallel-agents` | Phase A, Phase B | 依存のないタスクの並列 dispatch |
| `superpowers:requesting-code-review` | 全タスク完了後 | ブランチ全体のコードレビュー |
| `superpowers:finishing-a-development-branch` | レビュー完了後 | マージ/PR/クリーンアップ |

### ワークフロー

```
1. Plan file を読む (本ファイル)
2. Todo list を作成 (全8タスク)
3. Phase A を並列 dispatch (FG-06, FG-07, FG-08, FG-09)
   ├── 各タスク: implementer subagent → task-reviewer → fix if needed
   ├── Progress ledger に記録
   └. 完了後 Phase B へ
4. Phase B を並列 dispatch (FG-10, FG-11)
5. Phase C を順次 dispatch (FG-12)
6. Phase D を順次 dispatch (FG-13)
7. requesting-code-review で最終レビュー
8. finishing-a-development-branch で統合
```

### Model Selection

| タスク種別 | 推奨 model | 理由 |
|---|---|---|
| 機械的修正 (FG-08, FG-11) | cheap | 1-2ファイル、明確な spec |
| 分解・改善 (FG-07, FG-12) | standard | 複数関数の抽出、テスト改善 |
| セキュリティ (FG-09) | standard | CORS/API key、既存 pattern 従属 |
| State machine (FG-06) | standard | TRANSITIONS dict 修正、テスト修正 |
| Surrogate (FG-10) | cheap | STL normal 修正、ドキュメント追加 |
| Docs (FG-13) | cheap | Markdown 更新のみ |
| 最終レビュー | most capable | ブランチ全体の品質ゲート |

### Progress Ledger

`.superpowers/sdd/progress.md` に進捗を記録する。各タスク完了後:
```
Task FG-06: complete (commits abc1234..def5678, review clean)
Task FG-07: complete (commits ghi9012..jkl3456, review clean)
...
```

## Global Constraints

- `uv run pytest -q` は全タスクで通ること。テスト数は現行210以上を維持する。
- `bash ./run_cad_agent.sh validate-docs` は全タスクで通ること。
- `git diff --check` は全タスクで通ること。
- 既存のapproval_requiredスコープを拡張しない。
- production deployment、real LLM endpoint、real worker pool を追加しない。
- Design Doc (`docs/cad_agent_detailed_design.md`) との整合性を各タスクで確認する。
- **ワークツリーは使用しない。** 全作業はメインブランチで実行する。

## Task Index

| Task ID | Title | Priority | Dependencies | Model |
|---|---|---|---|---|
| `CAD-FG-06` | Orchestrator state machine 整合 | High | None | standard |
| `CAD-FG-07` | validate_artifacts() 分解 | High | None | standard |
| `CAD-FG-08` | DSL compiler cleanup | Medium | None | cheap |
| `CAD-FG-09` | Security hardening | High | None | standard |
| `CAD-FG-10` | Surrogate quality | Medium | None | cheap |
| `CAD-FG-11` | Error handling expansion | Medium | None | cheap |
| `CAD-FG-12` | Test quality improvement | Medium | FG-06, FG-07 | standard |
| `CAD-FG-13` | Documentation alignment | Low | All above | cheap |

## Execution Order

1. **Phase A (Parallel):** CAD-FG-06, CAD-FG-07, CAD-FG-08, CAD-FG-09 — 独立した変更なので並列実行可能
2. **Phase B (Parallel):** CAD-FG-10, CAD-FG-11 — Phase A完了後に実行
3. **Phase C (Sequential):** CAD-FG-12 — Phase A/Bの変更を反映したテスト改善
4. **Phase D (Final):** CAD-FG-13 — 全タスク完了後のドキュメント整合

## Per-Task Dispatch Template

各タスクの dispatch 時に使用するテンプレート:

```
You are implementing Task {TASK_ID} in the CAD-REVIEW-01 batch.

Context:
- Project: CADAGENT mechanical design platform
- This task fixes: {one-line description}
- Files to modify: {file list from task plan}
- Global constraints: uv run pytest -q must pass, validate-docs must pass, git diff --check must pass

Read the task brief: {brief file path}
Read the report template: {report file path}

Instructions:
1. Follow TDD: write failing test → verify fail → implement → verify pass → commit
2. Run validation commands after each change
3. Write results to report file
4. Return status, commits, test summary, and any concerns
```

## Review Findings Summary

### 1. 機能不足 (Insufficient Functionality)
- `CREATED → VALIDATION_FAILED` transition が TRANSITIONS にあるが handle_validation() で明示的に拒否
- DFM/AM check が `fdm_standard` のみ対応 (bug: other profiles always fail)
- BOOLEAN_FAILED, KERNEL_TIMEOUT error code が未定義
- CORS support が API server にない

### 2. 要件不適合 (Non-compliance)
- Deterministic surrogate STEP が実際のgeometryではなくテキスト
- Human approval が spec/material/manufacturing 変更で未適用
- Assembly/Motion validation が main pipeline から分離

### 3. 非効率 (Inefficiency)
- `validate_artifacts()` が290行の単一関数
- `_append_audit_record()` が `datetime.now()` を2回呼び出し (timestamp drift risk)
- `motion_validation._base_report()` が defaults を作成後即上書き

### 4. 低品質 (Low Quality)
- `_resolve_dimension()` が `parameter_name` を受け取り即削除 (dead parameter)
- Test が private `_transition()` API を直接使用
- Golden fixtures が production module に混在
- Surrogate STL normals が全て zero vectors (invalid)
- API server `do_PATCH`/`do_PUT` が `do_POST` に委譲 (confusing)
- CAD build path の broad exception catch が RuntimeError を逃す

## Completion Deviation Check

Before marking this review batch complete:

- `docs/cad_agent_detailed_design.md` との整合性を確認
- `docs/cad_agent_implementation_plan.md` との整合性を確認
- production deployment, real LLM, real worker の境界を侵していないことを確認
- `validate-docs` と `git diff --check` が通ることを確認
- `TASKS.md` が最終結果を記録していることを確認
- Progress ledger が全タスクを complete として記録していることを確認

## Required Validation Commands

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_review_phase1
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_review_phase2
bash ./run_cad_agent.sh serve --dry-run
git diff --check
```

# CAD-FG-13 — Documentation Alignment

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Design Doc のアーキテクチャ図と実装を整合させ、API key 設定方法をドキュメント化する。

**Architecture:** `docs/cad_agent_detailed_design.md` のアーキテクチャ図を実装に合わせて更新し、`docs/operations_ja.md` に API key/CORS 設定を追記する。

**Tech Stack:** Markdown.

## Global Constraints

- `bash ./run_cad_agent.sh validate-docs` → pass
- `git diff --check` → pass
- 既存のドキュメント構造を壊さない
- Design Doc の section 番号を変更しない

## superpowers Skill Integration

**Execution method:** `superpowers:subagent-driven-development`

- **Implementer dispatch:** Markdown 更新のみのため TDD 不要
- **Task review:** `superpowers:subagent-driven-development` の task-reviewer で spec compliance を確認
- **Model:** cheap (Markdown 更新のみ)
- **Workspace:** ワークツリー不使用。メインブランチで直接実行
- **Progress ledger:** `.superpowers/sdd/progress.md` に記録
- **Depends on:** CAD-FG-06 through CAD-FG-12 全完了後に実行

### Dispatch Prompt

```
Task: CAD-FG-13 — Documentation alignment
Plan: docs/cadagent_plans/CAD-FG-13/implementation-plan.md

You are implementing Task CAD-FG-13 in the CAD-REVIEW-01 batch.
This task aligns documentation with implementation.

Files to modify:
- docs/cad_agent_detailed_design.md (architecture diagram)
- docs/operations_ja.md (API key/CORS config)
- TASKS.md (status updates)

Global constraints:
- bash ./run_cad_agent.sh validate-docs → pass
- git diff --check → pass
- Do not change existing doc section numbers

Instructions:
1. Update architecture diagram to match implementation
2. Add API key configuration and CORS sections to operations_ja.md
3. Update TASKS.md with CAD-FG-06~13 completion status
4. Run bash ./run_cad_agent.sh validate-docs after changes
5. Write results to report file
6. Return status, commits, and any concerns
```

## Current Status

- Not started.
- Classification: `executable_now` — docs update, depends on CAD-FG-06 through CAD-FG-12.

## Tasks

### Task 13.1 — Update architecture diagram

**Files:**
- Modify: `docs/cad_agent_detailed_design.md`

**Problem:** アーキテクチャ図が実装フローと一致していない。

- [ ] **Step 1: Review current architecture diagram**

Read `docs/cad_agent_detailed_design.md` and identify the architecture section.

- [ ] **Step 2: Update diagram to match implementation**

Ensure the diagram reflects:
- Requirement Extractor → Spec Composer → DSL Compiler → CAD Runtime → Validation → Export pipeline
- Orchestrator state machine with correct states
- Assembly and Motion validation as parallel paths
- Security policy integration points

- [ ] **Step 3: Run docs validation**

Run: `bash ./run_cad_agent.sh validate-docs`
Expected: pass

### Task 13.2 — Document API key and CORS configuration

**Files:**
- Modify: `docs/operations_ja.md`

- [ ] **Step 1: Add API key configuration section**

```markdown
## API Key Configuration

デフォルトの API key は `local-dev-key` です。環境変数 `CAD_AGENT_API_KEY` で上書きできます:

```bash
export CAD_AGENT_API_KEY="your-custom-key"
```

開発環境以外では、必ず API key を変更してください。
```

- [ ] **Step 2: Add CORS configuration section**

```markdown
## CORS Configuration

API server はデフォルトで CORS を有効にしています:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, X-API-Key`

本番環境では `Access-Control-Allow-Origin` を适当的なドメインに制限してください。
```

- [ ] **Step 3: Run docs validation**

Run: `bash ./run_cad_agent.sh validate-docs`
Expected: pass

### Task 13.3 — Update TASKS.md with final status

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Update all CAD-FG-06 through CAD-FG-13 status**

Mark each task as completed with validation evidence.

- [ ] **Step 2: Add review batch summary**

```markdown
## Code Review改善 batch (CAD-REVIEW-01)

- [x] CAD-FG-06 — Orchestrator state machine 整合
- [x] CAD-FG-07 — validate_artifacts() 分解
- [x] CAD-FG-08 — DSL compiler cleanup
- [x] CAD-FG-09 — Security hardening
- [x] CAD-FG-10 — Surrogate quality
- [x] CAD-FG-11 — Error handling expansion
- [x] CAD-FG-12 — Test quality improvement
- [x] CAD-FG-13 — Documentation alignment
```

- [ ] **Step 3: Commit**

```bash
git add docs/ TASKS.md
git commit -m "docs: align architecture diagram, document API key/CORS config, update task status"
```

## Completion Deviation Check

- アーキテクチャ図が実装と一致していることを確認
- API key/CORS 設定が `operations_ja.md` に記載されていることを確認
- `TASKS.md` が最終結果を記録していることを確認
- `validate-docs` が通ることを確認

## Required Validation Commands

```bash
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh status
git diff --check
```

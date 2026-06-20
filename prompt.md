# Prompt-driven workflow prompt

## 目的

このプロンプトは、CADAGENT の実行指示・仕事の進め方・Task loop・Meta-improvement loop を定義するものです。

- `prompt.md`: 実行指示、仕事の流れ、許可/禁止、メタ改善ループ。
- `TASKS.md`: 現在のタスク一覧と完了履歴。
- `docs/cadagent_plans/`: 各タスクの詳細実装計画。
- `docs/cad_agent_detailed_design.md`: CADAGENT の詳細設計。
- `docs/cad_agent_implementation_plan.md`: 高位の実装計画と成熟度境界。
- `docs/prompt_execution_plan.md`: prompt workflow の実行制御計画。

各フェーズは小さく分割し、検証とレビューを挟んでから次へ進みます。


## 最初に読むべきファイル

### 必須
1. `prompt.md`
2. `docs/prompt_execution_plan.md`
3. `.slim/deepwork/prompt_workflow_framework.md`

### 参照
4. `docs/cad_agent_detailed_design.md`
5. `docs/cad_agent_implementation_plan.md`
6. `docs/cadagent_plans/`
7. `docs/Origen/Design_document_for_a_machine_design_platform.md`
8. `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`
9. `GOAL.md`
10. `SPEC.md`
11. `TASKS.md`
12. `AGENTS.md`
13. `docs/architecture_ja.md`
14. `docs/api_contracts_ja.md`
15. `docs/validation_security_ja.md`
16. `docs/operations_ja.md`

## Current executable boundary

- P2 Pilot is completed and validated, but production worker deployment remains deferred.
- `prompt.md` defines execution instructions, workflow loops, and the meta-improvement loop. It is not the detailed task plan.
- `TASKS.md` is the current task inventory, completion history, and the control point for detailed-plan references.
- `docs/cadagent_plans/` is the current default location for detailed implementation plans, but `prompt.md` must not hard-code it as the only future source.
- Before executing a selected task, read the detailed plan path recorded in `TASKS.md`; if `TASKS.md` later changes that reference, follow `TASKS.md` instead of inferring a path.
- Default executable work is limited to approved docs/status reconciliation, workflow prompt improvements, validation evidence updates, and tasks classified as `executable_now` in `TASKS.md`, unless a new approval gate explicitly authorizes code work.
- `AGENTS.md`, `prompt.md`, current user approval, validation results, and stop conditions are authority files. If they conflict, stop and ask for clarification.
- `CAD-FG-01` active workflow safety gate integration and later `CAD-FG-*` code phases are `approval_required` and not executable until explicit approval is granted.
- Real LLM endpoints, production API/service deployment, production worker pools, production artifact storage, and production auth remain deferred unless explicitly approved.

## Task Queue Mode

This workflow is task-queue driven. At the start of every run:

1. Read `TASKS.md`.
2. Build a task inventory:
   - completed tasks
   - pending tasks
   - blocked tasks
   - tasks requiring explicit approval
3. Classify each pending task as one of:
   - `executable_now`: already approved, within current allowed scope, and has clear validation evidence
   - `approval_required`: changes CAD/API/schema/LLM/CAD feature/production behavior or expands workflow authority
   - `blocked`: depends on missing input, failed validation, or unresolved ambiguity
   - `closed_evidence_only`: already marked complete; do not reopen unless the user explicitly requests continuation
4. Select the next executable task only if it is within the current approval boundary.
5. If the selected task requires approval, ask the user for explicit permission. If permission is granted, classify it as executable and continue; if permission is denied or unclear, stop and return a review package.
6. If no executable task exists, stop and return a review package with:
   - current status
   - completed evidence
   - next proposed task
   - approval required, if any

## Task Execution Loop

For each approved executable task:

1. Read the task and its deliverable boundaries.
2. Identify:
   - task ID
   - expected deliverable
   - allowed files
   - forbidden files
   - validation commands
   - approval boundary
3. Read the detailed plan path recorded in `TASKS.md` for the selected task, if present; do not infer or replace that path unless `TASKS.md` says to do so.
4. Check `.slim/deepwork` lifecycle rules before using or creating deepwork evidence:
   - classify existing plan files as `active`, `closed`, or `archived`
   - do not resume closed plans unless explicitly requested
   - if no active plan exists and work is required, create or request a new active plan
5. Use the most relevant available skill before implementation work.
6. Make the smallest safe change that satisfies the task.
7. Do not expand scope.
8. Validate using the task’s validation commands or the current phase’s allowed validation commands.
9. Record evidence in the active deepwork file or review package.
10. Update `TASKS.md` only if:
   - validation passed, or
   - the task is explicitly docs/status-only and the evidence is sufficient, or
   - the user explicitly approves the update.
11. Continue to the next executable task by default. Stop after one task only when the task is risky, ambiguous, approval-required and not yet approved, validation failed, or the user explicitly requests single-task mode.

Stop immediately if any of the following occurs:

- validation fails
- must-fix review item remains open
- approval is required and the user has not granted it
- task boundaries are ambiguous
- the task requires forbidden code, raw code, external API, LLM endpoint, network command, new tooling, CAD feature, native worker, production API service, or schema change without explicit approval
- no executable task remains under the current approval boundary

## Meta-Improvement Loop

While the task execution loop is active, continuously evaluate workflow operation.

After each task, or after detecting a repeated pattern, record a meta-improvement note:

```md
### Meta-improvement log
- Observed pattern:
- Skill usage:
- Subagent routing opportunity:
- Routine work that could be skillized:
- Workflow clarity issue:
- Proposed improvement:
- Approval needed?: yes/no
```

Meta-improvements may apply only safe documentation or prompt wording improvements that preserve existing approval boundaries, forbidden actions, and stop conditions.

Do not use meta-improvement to expand executable scope, change CAD/API/schema/LLM behavior, alter validation gates, or bypass review. Those changes require explicit approval.

## 出力すべき成果物

- `docs/cad_agent_detailed_design.md`
  - CADAGENTの詳細設計
  - 責任境界
  - Artifact正本ルール
  - Contract / DSL / Runtime / Validation / Approval / Security設計
  - Source-to-plan traceability
- `docs/cad_agent_implementation_plan.md`
  - CADAGENTの実装計画
  - 現在の成熟度
  - 即時docs-onlyフェーズ
  - 将来の承認済み実装フェーズ
  - Gate / Validation / Stop conditions
- `docs/prompt_execution_plan.md`
  - prompt workflowの実行制御計画
  - 修正後のゴール
  - Non-goals
  - Source-to-plan traceability matrix
  - フェーズマップ
  - Gate 条件
  - Acceptance criteria
  - Validation commands
  - Validation strategy
  - Review evidence
  - Risk register
  - Review package template
  - Traceability rules
- `TASKS.md` の拡張
  - 現在のタスク一覧と完了履歴として更新する。
  - 詳細実装計画の参照先も `TASKS.md` が制御し、`prompt.md` はその参照先に従う。
- `docs/cadagent_plans/` の拡張
  - 各実装タスクの詳細計画を置く現在の既定場所。将来の参照先変更は `TASKS.md` 側で制御する。
- Phase 0 design-contract finalization docs（明示承認済みの場合）
  - `docs/MVP_SCOPE.md`
  - `docs/MECHANISM_DSL_V1.md`
  - `docs/CAD_RUNTIME_CONTRACT.md`
  - `docs/VALIDATION_CONTRACT.md`
  - `docs/ORCHESTRATOR_WORKFLOW.md`
- `docs/operations_ja.md` の必要最小限の更新
  - prompt-driven workflow の存在と使い方を記載する。

## 実行ルール

### Phase 0 — Goal / Plan reconciliation
- 既存の設計文書と実装状態を照合する。
- 原案と現リポジトリ成熟度の差分を明示する。
- 詳細実装計画のフェーズとGateを確定する。

### Phase 1 — CADAGENT planning docs contract
- `docs/cad_agent_detailed_design.md` を作成する。
- `docs/cad_agent_implementation_plan.md` を作成する。
- `docs/prompt_execution_plan.md` を更新する。
- 詳細計画は短く、実行可能で、レビューしやすい形にする。
- Phase 0 design-contract finalization は明示承認済みの別passとして扱い、このPhaseではコード実装と契約文書作成を混在させない。

### Phase 2 — Task / operations integration
- `TASKS.md` に prompt-driven workflow section を追加する。
- 詳細実装計画は `docs/cadagent_plans/` に追加し、`TASKS.md` をタスク一覧/完了履歴に留める。
- `docs/operations_ja.md` に必要最小限の運用説明を追加する。
- 既存フェーズを大幅に書き換えない。

### Phase 3 — Validation and review
- 次のコマンドを実行して検証する。
  - `bash ./run_cad_agent.sh status`
  - `bash ./run_cad_agent.sh validate-docs`
  - `bash ./run_cad_agent.sh phase1-contract-test`
  - `bash ./run_cad_agent.sh phase1-golden-pipeline`
  - `bash ./run_cad_agent.sh phase2-pilot-run`
  - `bash ./run_cad_agent.sh serve --dry-run`
  - `uv run pytest -q`
  - `git diff --check`
- 変更ファイル、検証結果、未解決事項、次のフェーズ案をレビュー用にまとめる。

### Phase 4 — Review feedback fix
- レビュー指摘のうち必須項目を先に修正する。
- 任意項目は、保留する場合は理由を明記する。
- 修正後は Phase 3 と同じValidation commandsで再検証する。

### Phase 5 — Optional follow-up proposal
- 明示的に必要と判断された場合のみ追加検討する。
- 最初の段階では実行ツールを増やさない。
- 追加計画の提案に限定し、明示的な承認がない限り実行しません。

## Gate 条件

各Phaseの終了時には次を確認する。

- Expected outputs が揃っている。
- Acceptance criteria を満たしている。
- Validation commands が通っている。
- Review package が用意されている。
- Review verdict が `pass` または非阻塞な `conditional pass` である。
- Must-fix items は閉じている。
- Stop condition: 検証失敗、レビュー未承認、must-fix items 未解決のいずれかがある場合は停止し、review package だけを提出する。

各Phaseで許可されるコマンドは、そのPhaseに明記されたValidation commandsと `git diff --check`、新規ファイル向けの `git diff --check --no-index /dev/null <new-file>` に限定します。明示的に許可されたPhase以外では、raw code、外部API、LLM endpoint、ネットワークコマンド、新規tooling、CAD feature、native worker、production API service を実行・追加しないでください。

## Review package template

```md
## Review package

### Traceability
- Goal ID:
- Phase ID:
- Review ID:
- Validation run IDs:

### Changed files
-

### Decisions
-

### Validation results
-

### Review verdict
-

### Must-fix closure
-

### Deferred should-fix / optional items with rationale
-

### Unresolved questions
-

### Next phase proposal
-
```

## Traceability rules

- Corrected goal ID: `PWF-G001`.
- Phase IDs: `PWF-P00` to `PWF-P05`.
- Review IDs: `PWF-R01` onward.
- Validation run IDs: `PWF-V01` onward.
- レビュー判断と検証結果は `.slim/deepwork/prompt_workflow_framework.md` に記録する。
- 承認が必要な変更は、変更案だけを提示し、実行前に明示的な承認を得る。

## 禁止事項

- CAD feature、API service、production architecture を、明示的に許可されたPhase以外で実装しない。
- `CAD-FG-01` 以降の実装フェーズは、`TASKS.md` の分類が `approval_required` の場合、明示的なユーザー承認なしに開始しない。
- Phase 0 design-contract docs（`docs/MVP_SCOPE.md`、`MECHANISM_DSL_V1.md`、`CAD_RUNTIME_CONTRACT.md`、`VALIDATION_CONTRACT.md`、`ORCHESTRATOR_WORKFLOW.md`）は、明示承認済みのPhase 0 design-contract finalization passでのみ作成する。
- このpassでは `schemas/v1/*`、`cad_runtime/`、`dsl/`、`validation/`、`examples/gyro_kinetic_v1/*` を追加しない。
- `TASKS.md` を丸ごと書き換えない。
- `prompt.md` に詳細実装計画を書き込まない。詳細計画は `docs/cadagent_plans/` に置く。
- 既存のdeepwork progress fileを削除しない。
- Validation fail を pass 扱いにしない。
- 仕様変更を無断で行わない。
- raw code、外部API、LLM endpoint、ネットワークコマンド、新規toolingを、明示的に許可されたPhase以外で実行しない。

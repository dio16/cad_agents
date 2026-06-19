# Prompt-driven workflow prompt

## 目的

このプロンプトは、`docs/Origen/cad_agent_design_spec_and_implementation_plan.md` の原案をもとに、CADAGENTの詳細設計書・実装計画書を作成し、prompt-driven workflow framework の詳細計画を立て、各フェーズを安全に実行するための運用指示です。

このpassの目的はCADAGENT実装そのものではなく、詳細設計書・実装計画書・Gate・Validation・Review evidence の作成です。

## 重要方針

- 最初に行うべきことは、CAD機能・APIサービス・Production v1をいきなり実装することではありません。
- まず行うべきことは、prompt-driven workflow framework を構築することです。
- `docs/prompt_execution_plan.md` はprompt workflowの実行制御計画です。CADAGENTの詳細設計は `docs/cad_agent_detailed_design.md`、実装計画は `docs/cad_agent_implementation_plan.md` に置きます。
- 各フェーズは小さく分割し、検証とレビューを挟んでから次へ進みます。
- このpassはdocs-only workflowです。`validate-docs`を維持するためのvalidation-harness更新のみ許可します。
- 詳細な禁止事項は「禁止事項」セクションに従います。

## 最初に読むべきファイル

### 必須
1. `prompt.md`
2. `docs/prompt_execution_plan.md`
3. `.slim/deepwork/prompt_workflow_framework.md`

### 参照
4. `docs/cad_agent_detailed_design.md`
5. `docs/cad_agent_implementation_plan.md`
6. `docs/Origen/Design_document_for_a_machine_design_platform.md`
7. `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`
8. `GOAL.md`
9. `SPEC.md`
10. `TASKS.md`
11. `AGENTS.md`
12. `docs/architecture_ja.md`
13. `docs/api_contracts_ja.md`
14. `docs/validation_security_ja.md`
15. `docs/operations_ja.md`

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
  - 既存フェーズを壊さず、prompt-driven workflow section を追加する。
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
- `docs/operations_ja.md` に必要最小限の運用説明を追加する。
- 既存フェーズを大幅に書き換えない。

### Phase 3 — Validation and review
- 次のコマンドを実行して検証する。
  - `bash ./run_cad_agent.sh status`
  - `bash ./run_cad_agent.sh validate-docs`
  - `bash ./run_cad_agent.sh phase1-contract-test`
  - `bash ./run_cad_agent.sh phase1-golden-pipeline`
  - `bash ./run_cad_agent.sh phase2-pilot-run`
  - `uv run pytest -q`
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
- Phase 0 design-contract docs（`docs/MVP_SCOPE.md`、`MECHANISM_DSL_V1.md`、`CAD_RUNTIME_CONTRACT.md`、`VALIDATION_CONTRACT.md`、`ORCHESTRATOR_WORKFLOW.md`）は、明示承認済みのPhase 0 design-contract finalization passでのみ作成する。
- このpassでは `schemas/v1/*`、`cad_runtime/`、`dsl/`、`validation/`、`examples/gyro_kinetic_v1/*` を追加しない。
- `TASKS.md` を丸ごと書き換えない。
- 既存のdeepwork progress fileを削除しない。
- Validation fail を pass 扱いにしない。
- 仕様変更を無断で行わない。
- raw code、外部API、LLM endpoint、ネットワークコマンド、新規toolingを、明示的に許可されたPhase以外で実行しない。

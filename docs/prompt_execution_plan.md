# Prompt-driven execution plan

## Traceability

- Plan ID: `PWF-001`
- Source proposal: `docs/Origen/Design_document_for_a_machine_design_platform.md`
- Implementation plan source: `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`
- Workflow prompt: `prompt.md`
- Progress record: `.slim/deepwork/prompt_workflow_framework.md`
- Review IDs: `PWF-R01` onward
- Validation run IDs: `PWF-V01` onward

## Corrected goal

Goal ID: `PWF-G001`

このタスクの目的は、CADAGENTの実運用プラットフォーム全体を一度に実装することではありません。目的は、既存の設計文書・実装差分・プロジェクト方針決定・実装計画素案をもとに、CADAGENTの詳細設計書・実装計画書、およびprompt-driven workflow framework を構築することです。

このframeworkは、次のことを可能にします。

1. 現行ゴールと原案の差分を明示する。
2. 実装詳細計画をフェーズ単位に分解する。
3. 各フェーズにGate、Acceptance criteria、Validation commandsを設定する。
4. `prompt.md` に沿って1フェーズずつ実行する。
5. 検証結果とレビュー判断を記録し、次のフェーズに進む前に確認する。

## Non-goals

このpassでは、以下を実装しません。

- CAD feature、native CAD worker、`cad_runtime/cadquery_worker.py`、`dsl/op_registry.py`、`validation/geometry_checks.py`、`validation/dfm_fdm_checks.py` の実装。
- `schemas/v1/*`、`examples/gyro_kinetic_v1/*`、native worker pool、実LLM endpoint、production API service の追加。
- Production v1/v2 を本番実装として扱うこと。これらは現リポジトリでは skeleton / contract placeholder として扱います。

Phase 0 design-contract docs（`MVP_SCOPE.md`、`MECHANISM_DSL_V1.md`、`CAD_RUNTIME_CONTRACT.md`、`VALIDATION_CONTRACT.md`、`ORCHESTRATOR_WORKFLOW.md`）は、このprompt workflow passでは扱いません。明示承認済みのPhase 0 design-contract finalization passでは、実装コードではなく契約文書として作成可能です。

## Current maturity

現リポジトリは local CLI / PoC / Pilot maturity です。

- Phase 1 PoC: Requirement / Specification / Parametric DSL / Validation Report の contract、DSL AST、単一部品 golden pipeline、artifact hash index、human approval sample を検証可能。
- Phase 2 Pilot: FreeCAD/OCCT と Blender の executable probe、DFM/AM profile catalog、review diff HTML、audit JSONL、Model Gateway route trial を検証可能。
- Production v1/v2 items exist only as skeleton / contract placeholders, not as production-ready implementation.
- Native FreeCAD/OCCT/Blender、実 worker pool、実 LLM endpoints、PLM/ERP/MES、実 FEA、実 material DB、部品ライブラリ、BOM連携は将来拡張です。
- このpassの検証 evidence は `.slim/deepwork/prompt_workflow_framework.md` に記録します。

## Source-to-plan traceability matrix

| Source item | Current repo state | PWF phase | Output | Future work |
|---|---|---|---|---|
| Origen platform architecture | Docs only / partial skeleton | `PWF-P00`, `PWF-P01` | Architecture summary and planning traceability | Production v1/v2 implementation |
| CADAGENT Phase 0 design contracts | Deferred in this pass; approved Phase 0 finalization creates the five contract docs | `PWF-P01` | Deferred contract list and review notes only | Separate approved Phase 0 design-contract finalization pass |
| CADAGENT Phase 1 native CAD | PoC surrogate / golden path exists | `PWF-P00`, `PWF-P03` | Validation evidence and maturity statement | Native worker implementation |
| CADAGENT Phase 2 DFM/AM | Pilot probe/report exists | `PWF-P03` | Validation evidence and operations note | Stronger DFM/AM validation |
| LLM agents | Prompt/design boundary only | `PWF-P01`, `PWF-P02` | Workflow plan and execution prompt | Real LLM endpoint integration |

## Scope

In scope:

- `prompt.md` の更新。
- `docs/cad_agent_detailed_design.md` の作成。
- `docs/cad_agent_implementation_plan.md` の作成。
- `docs/prompt_execution_plan.md` の更新・整理。
- `TASKS.md` の拡張。
- `docs/operations_ja.md` の必要最小限の更新。
- `src/cad_agent/tools/validate_platform_contracts.py` の必要最小限の更新。
- 既存コマンドを使った検証。
- レビュー判断とtraceabilityの記録。

Out of scope for first pass:

- 新規CAD feature の実装。
- Production API service の追加。
- Native worker pool の追加。
- 実 LLM endpoint の統合。
- `TASKS.md` の全面書き換え。
- 既存deepwork progress file の削除。

## Non-goal enforcement

| Forbidden path / action | Forbidden action | Reason |
|---|---|---|
| `docs/Origen/` | Store detailed execution plan here | Origen remains source-material storage only. |
| `docs/MVP_SCOPE.md`, `MECHANISM_DSL_V1.md`, `CAD_RUNTIME_CONTRACT.md`, `VALIDATION_CONTRACT.md`, `ORCHESTRATOR_WORKFLOW.md` | 作成しない in this pass; approved Phase 0 finalization creates them docs-only | これらはCADAGENT実装契約文書であり、このprompt workflow passの対象外。明示承認済みのPhase 0 passでは実装コードではなく契約文書として作成可能。 |
| `schemas/v1/*` | Add or update | Schema implementation belongs to a future CADAGENT pass. |
| `cad_runtime/`, `dsl/`, `validation/` | Add implementation code | CAD feature and validation implementation are out of scope. |
| `examples/gyro_kinetic_v1/*` | Add example artifacts | First target examples are future implementation work. |
| Native worker pool, real LLM endpoint, production API service | Add or integrate | Production architecture is future scope. |
| `PWF-P05` | Execute without explicit approval | Optional tooling is proposal-only in this pass. |

## Common gate rule

Stop condition: 検証失敗、レビュー未承認、must-fix items 未解決のいずれかがある場合は停止し、review package だけを提出します。

## Phase map

### Phase 0 — Goal / Plan reconciliation (`PWF-P00`)

Expected outputs:

- 修正後ゴール。
- 現リポジトリ成熟度。
- フェーズマップ。
- Gate定義。

Acceptance criteria:

- 原案と現リポジトリの差分が明確。
- 最初のゴールがCADAGENT詳細設計・実装計画・prompt-driven workflow frameworkに限定されている。
- Phase 1以降の作業範囲が明示されている。

Gate:

- @oracle review を受ける。
- must-fix items を反映するまで次Phaseに進まない。

### Phase 1 — CADAGENT planning docs contract (`PWF-P01`)

Expected outputs:

- `prompt.md`
- `docs/cad_agent_detailed_design.md`
- `docs/cad_agent_implementation_plan.md`
- `docs/prompt_execution_plan.md`
- Source-to-plan traceability matrix
- Non-goal enforcement rules

Acceptance criteria:

- `prompt.md` は短く、実行可能で、安全制限を含む。
- `docs/cad_agent_detailed_design.md` はCADAGENTの詳細設計として利用可能。
- `docs/cad_agent_implementation_plan.md` はCADAGENTの実装計画として利用可能。
- `docs/prompt_execution_plan.md` はprompt workflowの実行制御計画として利用可能。
- Gate、Acceptance criteria、Validation commands、Review package template、Traceability rules を含む。
- Phase 0 design-contract docsは別passとして扱い、このPhaseでは契約文書と実装コードの作成・承認を混在させない。

Validation commands:

- `bash ./run_cad_agent.sh status`
- `bash ./run_cad_agent.sh validate-docs`
- `git diff --check --no-index /dev/null prompt.md`
- `git diff --check --no-index /dev/null docs/cad_agent_detailed_design.md`
- `git diff --check --no-index /dev/null docs/cad_agent_implementation_plan.md`
- `git diff --check --no-index /dev/null docs/prompt_execution_plan.md`

Gate:

- @oracle phase review を受ける。
- simplify/readability feedback を含む。
- must-fix items を修正するまで次Phaseに進まない。

### Phase 2 — Task / operations integration (`PWF-P02`)

Expected outputs:

- `TASKS.md` に prompt-driven workflow section を追加し、新しいCADAGENT planning docsを参照。
- `docs/operations_ja.md` に必要最小限の運用説明を追加。
- `src/cad_agent/tools/validate_platform_contracts.py` に新しいCADAGENT planning docsを追加。

Acceptance criteria:

- 既存Phase 0〜4 を壊さない。
- prompt-driven workflow が容易に見つかる。
- Production v1 scope を混入しない。

Validation commands:

- `bash ./run_cad_agent.sh status`
- `bash ./run_cad_agent.sh validate-docs`

Gate:

- @oracle phase review を受ける。
- must-fix items を修正するまで次Phaseに進まない。

### Phase 3 — Validation and review package (`PWF-P03`)

Expected outputs:

- 全検証結果。
- 変更ファイル一覧。
- 決定事項。
- 未解決事項。
- 次のPhase案。

Validation commands:

- `bash ./run_cad_agent.sh status`
- `bash ./run_cad_agent.sh validate-docs`
- `bash ./run_cad_agent.sh phase1-contract-test`
- `bash ./run_cad_agent.sh phase1-golden-pipeline`
- `bash ./run_cad_agent.sh phase2-pilot-run`
- `uv run pytest -q`

Gate:

- @oracle phase review を受ける。
- must-fix items を修正するまで次Phaseに進まない。

### Phase 4 — Review feedback fix (`PWF-P04`)

Expected outputs:

- レビュー指摘への対応。
- 再検証結果。
- 最終summary。

Acceptance criteria:

- 全must-fix items が解決済み。
- Should-fix items は解決済み、または理由付きで延期済み。
- 最終workflowが利用可能。

Validation commands:

- `bash ./run_cad_agent.sh status`
- `bash ./run_cad_agent.sh validate-docs`
- `bash ./run_cad_agent.sh phase1-contract-test`
- `bash ./run_cad_agent.sh phase1-golden-pipeline`
- `bash ./run_cad_agent.sh phase2-pilot-run`
- `uv run pytest -q`

Gate:

- @oracle final review を受ける。
- pass 判定または条件付きpassかつ未対応項目が非阻塞であることを確認する。

### Phase 5 — Optional tooling (`PWF-P05`)

Condition:

- docs-only workflow で不十分な場合のみ追加検討する。
- 明示的に必要と判断された場合のみ実行する。

Preferred first option:

- 既存 `run_cad_agent.sh` コマンドへの参照を整備する。
- 新規scriptは、明確な再現性上の利点がある場合のみ作成する。

## Validation strategy

- Phase gates use minimal validation: `status`, `validate-docs`, and targeted `git diff --check`.
- Final gate uses the full maintained validation set: `phase1-contract-test`, `phase1-golden-pipeline`, `phase2-pilot-run`, and `uv run pytest -q`.
- New files require `git diff --check --no-index /dev/null <new-file>` until they are tracked.
- Validation failures are never reclassified as pass. If a gate fails, stop and submit a review package only.

## Review evidence

Each phase review records:

- Review ID: `PWF-Rxx`
- Validation run IDs: `PWF-Vxx`
- Verdict: `pass`, `conditional pass`, or `blocked`
- Must-fix closure list
- Deferred should-fix / optional items with rationale
- Next phase proposal or stop reason

## Phase owners and delegates

- Orchestrator: phase sequencing, stop gates, and traceability.
- Docs writer: `prompt.md`, `docs/cad_agent_detailed_design.md`, `docs/cad_agent_implementation_plan.md`, `docs/prompt_execution_plan.md`, `TASKS.md`, `docs/operations_ja.md`, and the approved Phase 0 contract docs.
- Validator: validation commands and output capture.
- @oracle: plan and phase reviews with simplify/readability feedback.
- Human/reviewer: approval for scope changes or explicit out-of-scope work.

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

## Risk register

| Risk | Mitigation |
|---|---|
| Plan expands into full CADAGENT implementation | `PWF-G001` boundary and non-goal enforcement |
| Docs diverge from `prompt.md` | Keep `docs/cad_agent_detailed_design.md`, `docs/cad_agent_implementation_plan.md`, and `docs/prompt_execution_plan.md` cross-referenced. |
| Validation commands become too heavy | Minimal validation per phase; full validation at final gate |
| Stale Origen details copied into the prompt | Keep Origen as source material, not direct implementation source |
| Review feedback is not tracked | Review package template and `PWF-Rxx` / `PWF-Vxx` IDs |

## First-pass completion summary

Definition of done for this first pass:

- `prompt.md` exists as the root operational prompt.
- `docs/cad_agent_detailed_design.md` exists as the maintained detailed design document.
- `docs/cad_agent_implementation_plan.md` exists as the maintained implementation plan document.
- `docs/prompt_execution_plan.md` exists as the prompt workflow execution-control plan.
- `TASKS.md` and `docs/operations_ja.md` are extended without rewriting the existing Phase 0–4 roadmap.
- `validate-docs`, Phase 1/2 commands, `pytest`, and diff checks pass.
- Phase 5 optional tooling is deferred unless explicitly approved later.

## Decision log

| ID | Decision | Rationale |
|---|---|---|
| PWF-D001 | `prompt.md` は repo root に置く | ユーザーが `prompt.md` と明示しており、運用エントリポイントとして見つけやすいため。 |
| PWF-D002 | CADAGENT詳細設計は `docs/cad_agent_detailed_design.md` に置く | ユーザーが詳細設計書を明示的に要求しており、Origenには原案のみを残すため。 |
| PWF-D003 | CADAGENT実装計画は `docs/cad_agent_implementation_plan.md` に置く | ユーザーが実装計画書を明示的に要求しており、実行可能性とレビュー可能性を高めるため。 |
| PWF-D004 | `docs/prompt_execution_plan.md` はprompt workflowの実行制御計画にする | 詳細設計書・実装計画書とは役割を分離し、重複を避けるため。 |
| PWF-D005 | 初回実装は docs-only | 現リポジトリ成熟度を尊重し、過剰な自動化や新規実行ツールを避けるため。 |
| PWF-D006 | `TASKS.md` は拡張するが書き換えない | 既存Phase 0〜4 を壊さず、prompt-driven workflow を追加するため。 |
| PWF-D007 | 既存deepwork progress file は保持する | 過去の設計レビュー・実装履歴を失わないため。 |
| PWF-D008 | CADAGENT実装契約文書はこのprompt workflow passでは作成しない | 本passは詳細設計書・実装計画書に限定し、実装契約は承認済みPhase 0 design-contract finalization passへ任せるため。 |

# Tasks

## Meta: Prompt-driven workflow plan

- [x] Goal reconciliation: `PWF-G001` limits the immediate goal to CADAGENT detailed design + implementation plan docs and prompt-driven workflow, not full CAD platform implementation.
- [x] Root operational prompt: `prompt.md`
- [x] CADAGENT detailed design: `docs/cad_agent_detailed_design.md`.
- [x] CADAGENT implementation plan: `docs/cad_agent_implementation_plan.md`.
- [x] Prompt workflow execution control: `docs/prompt_execution_plan.md`.
- [x] Gate rules: Phase outputs, acceptance criteria, validation commands, review package, stop condition, and traceability IDs are defined.
- [x] First-pass scope: docs-only workflow, except validation-harness maintenance required for `validate-docs`; no new CAD features, production API service, native worker pool, or external LLM endpoint integration.
- [x] Final validation and @oracle final review: `status`, `validate-docs`, Phase 1/2 commands, `pytest`, and `git diff --check` pass.

## Prompt task-loop workflow

- [x] Confirm P2 Pilot completion status: P2-1 through P2-6 are complete and Phase 2 Pilot is validated; production worker deployment remains deferred.
- [x] `prompt.md` reads `TASKS.md` as the task inventory at the start of every run.
- [x] `prompt.md` classifies tasks as `executable_now`, `approval_required`, `blocked`, or `closed_evidence_only`.
- [x] `prompt.md` continues executing approved executable tasks by default; it stops only for validation failure, ambiguity, forbidden scope, no executable task, or ungranted approval requirement.
- [x] `prompt.md` respects `AGENTS.md` deepwork lifecycle rules before using or creating `.slim/deepwork` evidence.
- [x] `prompt.md` updates `TASKS.md` only after validation evidence, docs/status-only sufficiency, or explicit user approval.
- [x] `prompt.md` includes a meta-improvement loop for workflow clarity, skill usage, subagent routing, and routine skillization.
- [x] `prompt.md` asks for approval when a task requires explicit permission; if the user grants permission, the task loop continues with that task.
- [x] `prompt.md` stops when no executable task exists under the current approval boundary.
- [ ] Execute the next approved executable task from `TASKS.md` when explicit approval makes one available.
- [ ] Execute `CAD-P03` bounded workflow safety gate only after explicit approval.

## Status summary

- Phase 2 Pilot, Phase 3 Production v1 readiness skeleton, and Phase 4 Production v2 data-model stubs are implemented and validated.
- These completed phases remain skeleton/Pilot maturity only; production deployment, real worker pools, real LLM endpoints, production-grade material DB/adapters, FEA, and motion validation remain deferred.
- Current implementation work is status/documentation reconciliation only unless a new approval gate explicitly authorizes code work.

## CADAGENT phase implementation plans

- [x] Create nested plan folders under `docs/cadagent_plans/CAD-P00` through `CAD-P09`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P00/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P01/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P02/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P03/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P04/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P05/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P06/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P07/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P08/implementation-plan.md`.
- [x] Create per-phase detailed implementation plan: `docs/cadagent_plans/CAD-P09/implementation-plan.md`.
- [x] Add deviation-check requirement to each plan: verify against `docs/cad_agent_detailed_design.md`, `docs/cad_agent_implementation_plan.md`, phase non-goals, and deferred production boundaries before marking complete.
- [ ] Execute `CAD-P03` bounded workflow safety gate when explicitly approved.
- [ ] Update this file with each phase status: `not started`, `in progress`, `blocked`, or `completed`.
- [ ] Record each completed phase's validation commands, reviewer verdict, and deviation-check verdict.

## Phase 0: Design-contract finalization

- [x] Contract scope: Phase 0 is docs-only; no code under `cad_runtime/`, `dsl/`, `validation/`, `schemas/v1/*`, or example artifacts under `examples/gyro_kinetic_v1/*`.
- [x] `docs/MVP_SCOPE.md`: define contract MVP, target object, non-goals, manufacturing profiles, artifacts, acceptance criteria, and approval boundaries.
- [x] `docs/MECHANISM_DSL_V1.md`: define allowlist-first DSL v1, units, parameter references, feature order, derivative outputs, and extension governance.
- [x] `docs/CAD_RUNTIME_CONTRACT.md`: define native vs deterministic surrogate runtime, validated DSL input, artifact formats, metadata/hash, error codes, sandbox policy, audit, and no raw code.
- [x] `docs/VALIDATION_CONTRACT.md`: define validation as a gate, current checks, reason codes, maturity boundaries, override/escalation rules, and no failed-to-pass rewrites.
- [x] `docs/ORCHESTRATOR_WORKFLOW.md`: define state machine, max revision loop 3, escalation conditions, human approval events, traceability/audit obligations, and future-only API references.

## Phase 0: Repository alignment

- [x] 原案を正本として明示する。
- [x] 旧個別成果物のドキュメントを削除する。
- [x] 旧成果物生成・検証スクリプトを削除する。
- [x] 文書整合性チェック用スクリプトを追加する。

## Phase 1: PoC（6〜10週）

目的: 単一部品で、要件抽出から CAD 生成、検証、artifact 保存までの最小パイプラインを成立させる。

| ID | タスク | 完了条件 |
|---|---|---|
| P1-1 | Requirement JSON Schema | ✅ `cad_agent.platform_poc` の contract test で required fields と unknowns/assumptions 分離を確認 |
| P1-2 | Specification JSON Schema | ✅ `parameter_table`、`constraints`、`validation_plan` を contract test で確認 |
| P1-3 | Parametric DSL Schema | ✅ `units=mm`、parameter 参照整合、feature order、z軸方向のみ許可を AST validator で確認 |
| P1-4 | CAD Runtime MVP | ✅ allowlist DSL から STEP AP242 と STL を生成し、CadQuery export失敗は`EXPORT_FAILED`として返す |
| P1-5 | Validation MVP | ✅ bbox、volume、topology proxy、unit consistency、DFM/AM 最小ルールを Validation Report に保存 |
| P1-6 | Artifact Store MVP | ✅ `traceability_id` と `artifact_hash` を `artifact_index.jsonl` に保存し、hashを再計算 |
| P1-7 | Human Approval Gate | ✅ 仕様変更/validation override の承認記録を JSONL に保存 |

### Phase 1 hardening pass

- [x] Existing PoC/native CadQuery path のみを対象に、production worker/API/queue/auth/LLM endpoint を追加しない範囲で hardening 実施。
- [x] `step_ap242` を `derivative_outputs` に必須化し、z軸方向以外の feature axis を検証失敗にする。
- [x] parameter reference 文字列が numeric parameter に解決されることを AST validator で確認。
- [x] CadQuery STEP/STL export 失敗を `EXPORT_FAILED` validation failure として返す。
- [x] `phase1-contract-test` を一時出力ディレクトリで実行し、リポジトリ内の stale report を生成しない。
- [x] artifact hash 再計算と `cad_kernel` メタデータ確認を validation evidence に含める。

## Phase 2: Pilot（10〜16週）

目的: Phase 1 の単一部品パイプラインを維持したまま、実 worker 接続点、製造プロファイル、レビュー、監査、モデルルーティングを Pilot 用に通す。

- [x] Pilot implementation validated; production worker deployment remains future work.

| ID | タスク | 完了条件 |
|---|---|---|
| P2-1 | - [x] FreeCAD headless / OCCT worker probe | ✅ `phase2-pilot-run` で executable を検出した場合のみ native mode を記録し、未導入環境では deterministic surrogate adapter を記録 |
| P2-2 | - [x] Blender render / mesh worker probe | ✅ `phase2-pilot-run` で Blender adapter を probe し、native executable 不在時は OBJ surrogate mesh を生成 |
| P2-3 | - [x] DFM/AM プロファイルカタログ | ✅ `fdm_standard` / `cnc_3axis_soft_metal` の profile catalog を保持し、Pilot golden path では `fdm_standard` の仕様の壁厚・穴径・材料・`dfm.build_volume.max`（`max_bbox_mm` に対する保守的 axis-aligned bbox 比較）を検証 |
| P2-4 | - [x] Review UI、diff viewer、版比較 | ✅ Phase 1 baseline と revised spec の parameter diff を HTML review viewer に保存 |
| P2-5 | - [x] 監査ログ、保持期間、データ分類 | ✅ `audit_log.jsonl` に `data_classification`、`retention_days`、`model_route` を保存 |
| P2-6 | - [x] commercial / onprem / hybrid の Model Gateway 試験 | ✅ public commercial は許可、confidential commercial は onprem fallback として fail 判定 |

## Phase 3: Production v1 readiness skeleton

- [x] Skeleton implementation and contract coverage complete; production deployment remains deferred.

- [x] API Gateway / Project Service skeleton: stdlib HTTP server, in-memory project CRUD, API-key stub, artifact index lookup only.
- [x] Synchronous job queue simulation: `cad_golden`, `phase2_pilot`, and `validation` stub jobs with deterministic tests.
- [x] Security and observability skeleton: prompt/schema/code escape tests, Prometheus-text counters, `serve --dry-run`.
- [x] CI/SBOM/provenance skeleton: GitHub Actions smoke workflow, local deterministic SBOM/provenance commands.
- Deferred: Kubernetes, KServe/vLLM, Argo CD, Cosign/Trivy, real worker pools, real LLM endpoints, and production SLO enforcement.
- [x] CAD-P03 Task 03.1 — workflow state machine and audit event shape: `src/cad_agent/orchestrator.py`, `tests/test_orchestrator.py`; validation `uv run pytest tests/test_orchestrator.py -q`, `uv run pytest -q`, and `git diff --check`; reviewer verdict `pass` after fix round; forbidden production API/worker/schema scope check passed.
- [x] CAD-P03 Task 03.2 — enforce spec approval before CAD generation: `run_cad()` now requires current `spec_approved`; validation `uv run pytest tests/test_orchestrator.py -q`, `uv run pytest -q`, and `git diff --check`; reviewer verdict `pass`.
- [x] CAD-P03 Task 03.3 — convert validation failure to revision request: validation failures now create revision requests, store reason codes/failure locations, increment failure count, and escalate after three failures; validation `uv run pytest tests/test_orchestrator.py -q`, `uv run pytest -q`, and `git diff --check`; reviewer verdict `pass` after fix round.
- [x] CAD-P03 Task 03.4 — enforce export approval gate: `request_export()` now blocks without `validation_passed` or pending export approval; `approve_export()` moves `export_pending_approval` to `exported`; validation `uv run pytest tests/test_orchestrator.py -q`, `uv run pytest -q`, and `git diff --check`; reviewer verdict `pass` after fix round.
- [x] CAD-P03 Task 03.5 — integrate audit JSONL with Phase 2 style: `Workflow(audit_path=...)` now appends one JSON object per event with `event_type`, `type`, `traceability_id`, `timestamp`, `recorded_at`, `payload`, `retention_days`, and `data_classification`; validation `uv run pytest tests/test_orchestrator.py -q`, `uv run pytest -q`, and `git diff --check`; no production API/auth/worker/storage, real LLM endpoint, mechanism DSL, motion validation, FEA, or production CAD feature added.
- [ ] CAD-P03 Task 03.6 — close phase with deviation check.

## Phase 4: Production v2 data-model stubs

- [x] Skeleton implementation and contract coverage complete; production database/adapters/FEA remain deferred.

- [x] Static material catalog stub for `PLA`, `PETG`, `ABS`, `6061-T6`, `POM`, `17-4PH` with explicit `skeleton_stub` / reference-only metadata.
- [x] Decoupled BOM aggregation stub with validation errors, weight stub, and cost stub.
- [x] Axis-aligned bbox assembly interference/separation/adjacency stub; contact, motion, and FEA remain future work.
- Deferred: real material database, parts library, PLM/ERP/MES adapters, tenant isolation, regulatory workflow, and production-grade assembly/FEA validation.

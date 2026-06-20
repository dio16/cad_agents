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
- [x] `prompt.md` reads the detailed plan path recorded in `TASKS.md`; current plan entries point to `docs/cadagent_plans/<TASK_ID>/implementation-plan.md`.
- [x] `prompt.md` continues executing approved executable tasks by default; it stops only for validation failure, ambiguity, forbidden scope, no executable task, or ungranted approval requirement.
- [x] `prompt.md` respects `AGENTS.md` deepwork lifecycle rules before using or creating `.slim/deepwork` evidence.
- [x] `prompt.md` updates `TASKS.md` only after validation evidence, docs/status-only sufficiency, or explicit user approval.
- [x] `prompt.md` includes a meta-improvement loop for workflow clarity, skill usage, subagent routing, and routine skillization.
- [x] `prompt.md` asks for approval when a task requires explicit permission; if the user grants permission, the task loop continues with that task.
- [x] `prompt.md` stops when no executable task exists under the current approval boundary.
- [ ] Execute the next approved executable task from `TASKS.md` when explicit approval makes one available.
- [ ] Execute `CAD-FG-01` active workflow safety gate integration only after explicit approval.

## Task plan reference policy

- `prompt.md` must read task inventory from `TASKS.md` only.
- Detailed plan paths are controlled by `TASKS.md`.
- Current plan entries point to `docs/cadagent_plans/<TASK_ID>/implementation-plan.md`, but future reference changes must be made here first.
- `prompt.md` must not infer a different detailed-plan location unless `TASKS.md` records that location.

## Status summary

- [x] Phase 2 Pilot, Phase 3 Production v1 readiness skeleton, Phase 4 Production v2 data-model stubs, Phase 5 assembly AABB validation, Phase 6 mechanism DSL compiler, Phase 7 local/mock LLM-agent routes, Phase 8 bounded motion validation, and Phase 9 first target object integration are implemented and validated.
- These completed phases remain skeleton/Pilot maturity only where noted; production deployment, real worker pools, real LLM endpoints, production-grade material DB/adapters, FEA, production dynamic simulation, and production artifact storage remain deferred.
- Current implementation work is status/documentation reconciliation only unless a new approval gate explicitly authorizes code work.
- Functional gap implementation plan is recorded below as `CAD-FG-*`; code phases are `approval_required` and must not start without explicit user approval.

## Functional gap implementation plan

Detailed plan paths are controlled by this file. Current entries point to `docs/cadagent_plans/CAD-FG-*/implementation-plan.md`; if the reference location changes, update `TASKS.md` first.

- [ ] `CAD-FG-00` — Maintained-doc status drift reconciliation. Plan: `docs/cadagent_plans/CAD-FG-00/implementation-plan.md`. Classification: `executable_now`.
- [ ] `CAD-FG-01` — Active workflow safety gate integration. Plan: `docs/cadagent_plans/CAD-FG-01/implementation-plan.md`. Classification: `approval_required`.
- [ ] `CAD-FG-02` — Validation report and artifact metadata hardening. Plan: `docs/cadagent_plans/CAD-FG-02/implementation-plan.md`. Classification: `approval_required`.
- [ ] `CAD-FG-03` — Model Gateway and data-classification API integration. Plan: `docs/cadagent_plans/CAD-FG-03/implementation-plan.md`. Classification: `approval_required`.
- [ ] `CAD-FG-04` — Agent route hardening decision and implementation. Plan: `docs/cadagent_plans/CAD-FG-04/implementation-plan.md`. Classification: `approval_required`; real LLM endpoint integration requires separate explicit approval.
- [ ] `CAD-FG-05` — Production infrastructure deferral. Plan: `docs/cadagent_plans/CAD-FG-05/implementation-plan.md`. Classification: `blocked` until production-architecture approval.

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
- [x] Create per-task detailed implementation plan: `docs/cadagent_plans/CAD-FG-00/implementation-plan.md`.
- [x] Create per-task detailed implementation plan: `docs/cadagent_plans/CAD-FG-01/implementation-plan.md`.
- [x] Create per-task detailed implementation plan: `docs/cadagent_plans/CAD-FG-02/implementation-plan.md`.
- [x] Create per-task detailed implementation plan: `docs/cadagent_plans/CAD-FG-03/implementation-plan.md`.
- [x] Create per-task detailed implementation plan: `docs/cadagent_plans/CAD-FG-04/implementation-plan.md`.
- [x] Create per-task detailed implementation plan: `docs/cadagent_plans/CAD-FG-05/implementation-plan.md`.
- [x] Add deviation-check requirement to each plan: verify against `docs/cad_agent_detailed_design.md`, `docs/cad_agent_implementation_plan.md`, phase non-goals, and deferred production boundaries before marking complete.
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
- [x] CAD-P03 Task 03.5 — integrate audit JSONL with Phase 2 style: `Workflow(audit_path=...)` now appends one JSON object per event with `event_type`, `type`, `traceability_id`, `timestamp`, `recorded_at`, `payload`, `retention_days`, and `data_classification`; validation `uv run pytest tests/test_orchestrator.py -q`, `uv run pytest -q`, and `git diff --check`; reviewer verdict `pass`.
- [x] CAD-P03 Task 03.6 — close phase with deviation check: forbidden production API/worker/schema/real-LLM/mechanism/motion/FEA scope check passed (`git status --short -- api_server.py project_service.py job_queue.py schemas/v1 cad_runtime dsl` returned no changes); final validation passed with `uv run pytest -q` → `112 passed, 2 subtests passed`, `bash ./run_cad_agent.sh validate-docs` → pass, `bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_orchestrator_phase1` → pass, `bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_orchestrator_phase2` → pass, `bash ./run_cad_agent.sh serve --dry-run` → OK, `git diff --check` → pass; reviewer verdict `pass` after oracle result returned; deviation-check verdict `pass`.

## Phase 5: Assembly DSL and AABB validation

- [x] CAD-P05 Task 05.1 — approved assembly contract document: created `docs/ASSEMBLY_DSL_CONTRACT.md` with bounded scope, non-goals, part record, validation checks, report shape, and workflow gate rule; `bash ./run_cad_agent.sh validate-docs` → pass.
- [x] CAD-P05 Task 05.2 — AABB interference check: `src/cad_agent/assembly_checks.py` already provided deterministic AABB interference/separation logic; added `AABB_INTERFERENCE` reason code and validation-result adapter with reason codes/failure locations; `uv run pytest tests/test_assembly_checks.py -q` covered interference, separation, invalid bbox, and report dict shape.
- [x] CAD-P05 Task 05.3 — adjacency check: added `check_adjacency()` wrapper and tests for tolerance-based adjacency.
- [x] CAD-P05 Task 05.4 — connect assembly validation to workflow gate: added `Workflow.handle_assembly_validation()` and regression test proving assembly failure moves workflow to `revision_requested` and blocks export with `VALIDATION_NOT_PASSED`.
- [x] CAD-P05 Task 05.5 — close phase with deviation check: forbidden full B-Rep/motion/FEA/PLM scope check passed (`git status --short -- src/cad_agent/agents schemas/v1 cad_runtime dsl motion_validation.py` returned no changes); final validation passed with `uv run pytest tests/test_assembly_checks.py tests/test_orchestrator.py -q` → `31 passed`, `uv run pytest -q` → `125 passed, 2 subtests passed`, `bash ./run_cad_agent.sh validate-docs` → pass, `bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_assembly_phase1` → pass, `git diff --check` → pass; reviewer verdict `pass`; deviation-check verdict `pass`.

## Phase 4: Local API/project/job/artifact workflow v1

- [x] CAD-P04 Task 04.1 — local workflow run endpoint: `src/cad_agent/api_server.py`, `tests/test_api_server.py`; validation `uv run pytest tests/test_api_server.py -q` → `18 passed`, `uv run pytest -q` → `113 passed, 2 subtests passed`; reviewer verdict `pass`.
- [x] CAD-P04 Task 04.2 — local revision endpoint: deterministic `POST /v1/revisions` uses CAD-P03 `Workflow.request_revision()` and returns local `revision_requested` decision with reason codes and revision count; validation `uv run pytest tests/test_api_server.py -q` → `22 passed`, `uv run pytest -q` → `117 passed, 2 subtests passed`, `git diff --check` → pass.
- [x] CAD-P04 Task 04.3 — local export decision endpoint: deterministic `POST /v1/exports` and `POST /v1/approvals/export` use CAD-P03 `Workflow.request_export()` / `approve_export()` gates with in-memory local approval reset for tests; validation `uv run pytest tests/test_api_server.py -q` → `25 passed`, `uv run pytest -q` → `120 passed, 2 subtests passed`, `git diff --check` → pass; reviewer verdict `pass`.
- [x] CAD-P04 Task 04.4 — preserve health and metrics: added explicit `/health` + `/metrics` regression coverage; validation `uv run pytest tests/test_api_server.py -q` → `26 passed`, `uv run pytest -q` → `121 passed, 2 subtests passed`, `bash ./run_cad_agent.sh serve --dry-run` → OK, `git diff --check` → pass.
- [x] CAD-P04 Task 04.5 — close phase with deviation check: forbidden production deployment scope check passed (`git status --short -- .github k8s docker-compose.yml Dockerfile schemas/v1` returned no changes); final validation passed with `uv run pytest -q` → `121 passed, 2 subtests passed`, `bash ./run_cad_agent.sh serve --dry-run` → OK, `bash ./run_cad_agent.sh validate-docs` → pass, `git diff --check` → pass; reviewer verdict `pass`; deviation-check verdict `pass`.

## Phase 6: Mechanism DSL and deterministic compiler

- [x] CAD-P06 Task 06.1 — mechanism DSL allowlist: created `src/cad_agent/dsl_compiler.py` with `CompileResult`, `compile_mechanism_plan`, Phase 1 allowlist (`box`, `cylinder`, `through_hole`), raw-code rejection, and tests; validation `uv run pytest tests/test_dsl_compiler.py -q` → `3 passed`, `uv run pytest -q` → `128 passed, 2 subtests passed`, `git diff --check` clean; reviewer verdict `pass`; commit `3862a03`.
- [x] CAD-P06 Task 06.2 — compile approved mechanism plan: added bounded `shaft` mechanism operation, schema-valid traceability fallback, `positions_mm`/parameter validation, and `docs/MECHANISM_DSL_OPERATIONS.md`; validation `uv run pytest tests/test_dsl_compiler.py -q` → `9 passed`, `uv run pytest -q` → `134 passed, 2 subtests passed`, `git diff --check` clean; oracle re-review `pass`; commit `5a18a13`.
- [x] CAD-P06 Task 06.3 — validate compiler output with Phase 1 schema/AST: added integration validation helper/test proving compiler output passes Phase 1 validation; validation `uv run pytest tests/test_dsl_compiler.py -q` → `10 passed`, `bash ./run_cad_agent.sh phase1-contract-test` → pass, `uv run pytest -q` → `135 passed, 2 subtests passed`, `validate-docs` pass, `git diff --check` clean; reviewer verdict `pass`; commit `aadeb7e`.
- [x] CAD-P06 Task 06.4 — approval gate for new operations: added `NEW_OPERATION_APPROVAL_REQUIRED`, `request_new_operation(...)`, and `Workflow.request_new_operation_approval(...)`; validation `uv run pytest tests/test_dsl_compiler.py tests/test_orchestrator.py -q` → `34 passed`, `uv run pytest -q` → `138 passed, 2 subtests passed`, `git diff --check` clean; reviewer verdict `pass` after manual reconciliation of empty oracle output.
- [x] CAD-P06 Task 06.5 — close phase with deviation check: forbidden real-LLM/raw-code scope check passed (`git diff -- src/cad_agent/dsl_compiler.py src/cad_agent/agents` returned no changes); final validation passed with `uv run pytest -q` → `138 passed, 2 subtests passed`, `bash ./run_cad_agent.sh phase1-contract-test` → pass, `bash ./run_cad_agent.sh validate-docs` → pass, `git diff --check` → pass; reviewer verdict `pass`; deviation-check verdict `pass`.

## Phase 7: LLM agents and schema-retry routes

- [x] Skeleton implementation and contract coverage complete; production LLM endpoints, production model infrastructure, and raw-code execution remain deferred/forbidden.
- [x] Bounded local/mock agent route modules added under `src/cad_agent/agents/` for requirement extraction, specification composition, and mechanism planning.
- [x] Deterministic schema retry policy added for invalid JSON/schema outputs with structured failure reason codes.
- [x] Model routing policy enforces commercial/on-prem approval boundaries for confidential, regulated, and export-controlled data.
- [x] Agent route audit JSONL records route, model routing decision, data classification, retry/schema status, traceability, retention, and timestamps.
- [x] CAD-P07 Task 07.1 — local agent route skeletons: created `src/cad_agent/agents/{common,requirement_extractor,spec_composer,mechanism_planner}.py` and `tests/test_agents.py`; validation `uv run pytest tests/test_agents.py -q` → `4 passed`, `uv run pytest -q` → `142 passed, 2 subtests passed`, `git diff --check` clean; reviewer verdict `pass` after manual reconciliation of empty oracle output; commit `4be37d4`.
- [x] CAD-P07 Task 07.2 — schema retry policy: added deterministic `retry_schema(...)` and route integration; validation `uv run pytest tests/test_agents.py -q` → `8 passed`, `uv run pytest -q` → `146 passed, 2 subtests passed`, `git diff --check` clean; reviewer verdict `pass` after manual reconciliation of empty oracle output; commit `414ff4d`.
- [x] CAD-P07 Task 07.3 — model routing policy: added `ModelRouteDecision` / `route_model(...)`, integrated routing metadata, and security/agent tests; validation `uv run pytest tests/test_agents.py tests/test_security.py -q` → `18 passed`, `uv run pytest -q` → `152 passed, 2 subtests passed`, `git diff --check` clean; reviewer verdict `pass` after manual reconciliation of empty oracle output; commit `a446a99`.
- [x] CAD-P07 Task 07.4 — audit agent route decisions: added `write_agent_route_audit(...)`, integrated `audit_path` into route modules, and JSONL audit regression; validation `uv run pytest tests/test_agents.py -q` → `10 passed`, `uv run pytest -q` → `153 passed, 2 subtests passed`, `git diff --check` clean; reviewer verdict `pass` after manual reconciliation of empty oracle output; commit `c1c9dfc`.
- [x] CAD-P07 Task 07.5 — close phase with deviation check: forbidden production model endpoint/raw-code scope check passed (`git diff -- src/cad_agent/agents` returned no production model endpoint evidence); final validation passed with `uv run pytest -q` → `153 passed, 2 subtests passed`, `bash ./run_cad_agent.sh validate-docs` → pass, `bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_agents_phase2` → pass, `git diff --check` → pass; reviewer verdict `pass`; deviation-check verdict `pass`.

## Phase 8: Motion validation

- [x] Bounded motion-state input schema and deterministic validation report contract implemented.
- [x] Deterministic clearance rule added when `clearance_mm` / `min_clearance_mm` are provided; no FEA, production dynamic simulation, or sweep collision was added.
- [x] Motion validation failure is connected to the CAD-P03 workflow/export gate; motion pass does not approve export by itself.
- [x] CAD-P08 Task 08.1 — define motion validation input schema: created `docs/MOTION_VALIDATION_CONTRACT.md`, `src/cad_agent/motion_validation.py`, and `tests/test_motion_validation.py`; validation `uv run pytest tests/test_motion_validation.py -q` → `7 passed`, `git diff --check` clean; reviewer verdict `pass`; commit `d610987`.
- [x] CAD-P08 Task 08.2 — implement clearance check: added `INSUFFICIENT_CLEARANCE` and coupled clearance-field reason codes with tests and contract updates; validation `uv run pytest tests/test_motion_validation.py -q` → `14 passed`, `git diff --check` clean; reviewer verdict `pass`; commit `b514978`.
- [x] CAD-P08 Task 08.3 — produce motion validation report: added report-shape helper/tests and documented required report fields; validation `uv run pytest tests/test_motion_validation.py -q` → `15 passed`, `git diff --check` clean; reviewer verdict `pass`; commit `ee829c8`.
- [x] CAD-P08 Task 08.4 — connect motion failure to export gate: added `Workflow.handle_motion_validation(...)`, motion failure blocks export, motion pass does not replace CAD-P03 export approval; validation `uv run pytest tests/test_motion_validation.py tests/test_orchestrator.py -q` → `41 passed`, `git diff --check` clean; reviewer verdict `pass` after manual reconciliation of empty oracle output; commit `3336b10`.
- [x] CAD-P08 Task 08.5 — close phase with deviation check: forbidden FEA/production dynamic simulation/sweep scope check passed (`git diff -- src/cad_agent/motion_validation.py` returned only bounded deterministic schema/clearance/report logic); final validation passed with `uv run pytest -q` → `171 passed, 2 subtests passed`, `bash ./run_cad_agent.sh validate-docs` → pass, `bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_motion_phase1` → pass, `git diff --check` → pass; reviewer verdict `pass`; deviation-check verdict `pass`.

## Phase 9: First target object end-to-end integration

- [x] User explicitly approved `artifacts/gyro_kinetic_v1/target_spec.json を承認`; approved target spec includes `tr_target_gyro_kinetic_v1`, approval metadata, embedded requirement/specification/DSL, and validation plan.
- [x] Deterministic target artifacts added under `artifacts/gyro_kinetic_v1/`: `target_spec.json`, `requirement.json`, `specification.json`, and `dsl.json`.
- [x] Target requirement/specification are Phase 1 schema-valid; target DSL is Phase 1 schema/AST-valid using only `box` and z-axis `through_hole`.
- [x] Target CAD runtime generates metadata and validation report; export still requires CAD-P03 export approval after validation pass.
- [x] CAD-P09 Task 09.1 — approve target object spec: created `artifacts/gyro_kinetic_v1/target_spec.json` with deterministic approval metadata; validation `uv run pytest tests/test_target_object.py tests/test_orchestrator.py -q` → `34 passed`; reviewer verdict `pass`; commit `332400c`.
- [x] CAD-P09 Task 09.2 — generate requirement and specification artifacts: created schema-valid `requirement.json` and `specification.json`; validation `uv run pytest tests/test_target_object.py -q` → pass; reviewer verdict `pass`; commit `332400c`.
- [x] CAD-P09 Task 09.3 — compile target DSL and run CAD: created Phase 1-compatible `dsl.json`; target CAD run generates metadata; validation `bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_target_phase1` → pass; reviewer verdict `pass`; commit `332400c`.
- [x] CAD-P09 Task 09.4 — run validation and approval gate: added target-object tests proving validation pass and export approval gate; validation `uv run pytest tests/test_target_object.py tests/test_orchestrator.py -q` → `34 passed`; reviewer verdict `pass`; commit `332400c`.
- [x] CAD-P09 Task 09.5 — produce review package and close phase: added deterministic test review-package fixture with traceability; final validation passed with `bash ./run_cad_agent.sh status` → pass, `bash ./run_cad_agent.sh validate-docs` → pass, `bash ./run_cad_agent.sh phase1-contract-test` → pass, `bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_target_phase1` → pass, `bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_target_phase2` → pass, `bash ./run_cad_agent.sh serve --dry-run` → OK, `uv run pytest -q` → `179 passed, 2 subtests passed`, `git diff --check` → pass; reviewer verdict `pass` after oracle review `PASS_WITH_NOTES`; deviation-check verdict `pass`.

## Phase 4: Production v2 data-model stubs

- [x] Skeleton implementation and contract coverage complete; production database/adapters/FEA remain deferred.

- [x] Static material catalog stub for `PLA`, `PETG`, `ABS`, `6061-T6`, `POM`, `17-4PH` with explicit `skeleton_stub` / reference-only metadata.
- [x] Decoupled BOM aggregation stub with validation errors, weight stub, and cost stub.
- [x] Axis-aligned bbox assembly interference/separation/adjacency stub; contact, motion, and FEA remain future work.
- Deferred: real material database, parts library, PLM/ERP/MES adapters, tenant isolation, regulatory workflow, and production-grade assembly/FEA validation.

# CADAGENT Implementation Plan

## 1. Document status

- Status: maintained implementation planning artifact for `docs/cad_agent_detailed_design.md`
- Source: `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`
- Related detailed design: `docs/cad_agent_detailed_design.md`
- Scope boundary: this document defines bounded implementation phases, gates, validation commands, review packages, and traceability for CADAGENT. It does not authorize production CAD features, native worker deployment, production APIs, auth, worker queues, durable artifact storage, real LLM endpoints, `schemas/v1/*`, PLM/ERP/MES adapters, FEA, or motion validation unless a phase is explicitly approved.
- Current maturity: bounded PoC/Pilot/skeleton implementation; not a full design implementation.

## 2. How to use this plan

This plan is the execution roadmap for implementing `docs/cad_agent_detailed_design.md`. Each phase must be approved before execution. A phase is complete only when its entry criteria, exit criteria, validation gate, and review package are satisfied.

Document boundaries:

- `prompt.md` defines execution instructions, workflow loops, and the meta-improvement loop.
- `TASKS.md` records the current task inventory and completion history.
- `docs/cadagent_plans/` contains the detailed implementation plan for each task.
- `docs/cad_agent_implementation_plan.md` remains the high-level phase roadmap and maturity boundary.

Required phase fields:

- **Design coverage**: which detailed-design responsibilities are addressed.
- **Current status**: completed, skeleton, stub, not started, or in progress.
- **Implementation goal**: the bounded deliverable for this phase.
- **Non-goal**: work explicitly excluded from this phase.
- **Entry criteria**: prerequisites before implementation starts.
- **Exit criteria**: acceptance criteria required to close the phase.
- **Primary files**: likely source, test, docs, and validation files.
- **Gate**: review/approval required before moving to the next phase.
- **Deferred production boundaries**: production-grade work that remains out of scope.

## 3. Agent routing and execution rules

Use lane-specific agents instead of assigning all implementation work to one general agent.

- `fixer`: bounded implementation tasks with clear files, tests, and acceptance criteria.
- `oracle`: phase brief review, high-risk safety-gate review, task review for risky changes, and final whole-branch review.
- `designer`: UI/UX or review-interface polish only when user-facing layout, interaction, or visual hierarchy is in scope.
- `council`: only when independent high-risk architectural opinions are needed and disagreement is useful.
- `general`: reconnaissance, reconciliation, or non-specialist support; do not use as the default implementation lane for bounded code tasks.

Execution guardrails:

- Use `docs/cadagent_plans/<TASK_ID>/implementation-plan.md` as the task brief for implementation tasks.
- Use TDD for new behavior: write the failing test first, verify the expected failure, then implement the minimal passing code.
- Do not dispatch overlapping implementation agents against the same files or shared state.
- Review each task with a diff package before marking it complete.
- Record completed task commits and validation evidence in `.superpowers/sdd/progress.md` or the active deepwork/progress record.
- Treat `CAD-P03`, `CAD-P07`, and `CAD-P09` as high-risk phases requiring explicit safety/reviewer attention because they affect workflow gates, LLM routing, or target-object export decisions.
- Never let implementation convenience expand scope into production API/auth/worker/storage, real LLM endpoints, FEA, motion validation, PLM/ERP/MES adapters, or unapproved print/export.

## 3. Current repository maturity

| Area | Current state | Implementation implication |
|---|---|---|
| CLI | Present | Use `run_cad_agent.sh` as the local validation entrypoint. |
| Phase 1 PoC/native CadQuery path | Implemented and hardened | Use as the bounded deterministic CAD path for validation; production native worker deployment remains deferred. |
| Phase 2 DFM/AM Pilot | Implemented and validated | Use DFM/AM profile, review diff, audit, and gateway probes as local PoC/Pilot behavior. |
| Local API/project/job skeletons | Completed skeleton only | Use as local in-process workflow experiments only; not production API/service readiness. |
| Material/BOM/AABB stubs | Stub only | Use as reference data-model material only; production material DB, adapters, and full assembly validation remain deferred. |
| LLM endpoints | Local/mock agents only; real endpoints not integrated | Model Gateway remains policy/probe only until explicit approval. |
| Approval/revision/export gates | Local skeleton/stub only | Existing approval helpers and workflow state machine are validated locally; active golden/API enforcement remains `CAD-FG-01`. |
| Full design implementation | Not complete | Remaining phases below must be approved and executed one at a time. |

## 4. Phase matrix

| Phase ID | Phase name | Design coverage | Current status | Recommended order | Gate |
|---|---|---|---|---|---|
| `CAD-P00` | Source/design contract finalization | Planning contracts, traceability, stop conditions | Completed docs-only | Baseline | Reviewer approval |
| `CAD-P01` | Native CAD golden path hardening | CAD Runtime, artifact ownership, validation report | Completed/hardened PoC | Baseline | Reviewer approval |
| `CAD-P02` | DFM/AM validation pilot | DFM/AM validation, audit, model gateway probes | Completed Pilot | Baseline | Reviewer approval |
| `CAD-P03` | Bounded workflow safety gate | Orchestrator approval, revision loop, export gate, audit trail | Completed skeleton; production API/worker/schema scope deferred | After `CAD-P02` | Human/reviewer approval |
| `CAD-P04` | Local API/project/job/artifact workflow v1 | API skeleton, project service, job queue, artifact lookup | Completed skeleton; production deployment deferred | After `CAD-P03` | Reviewer approval |
| `CAD-P05` | Assembly DSL and AABB validation | Assembly placement, constraints, AABB checks | Completed skeleton; full B-Rep/motion/FEA/PLM deferred | After `CAD-P03`/`CAD-P04` | Reviewer approval |
| `CAD-P06` | Mechanism DSL and deterministic compiler | Mechanism plan, DSL operations, compiler service | Completed deterministic compiler; new-operation approval gate added | After `CAD-P05` or split into compiler-first phase | Reviewer approval |
| `CAD-P07` | LLM agents and schema-retry routes | Requirement Extractor, Spec Composer, Mechanism Planner, DSL Compiler proposals | Completed local/mock skeleton; production LLM endpoints deferred | After deterministic contracts/gates are stable | Human approval |
| `CAD-P08` | Motion validation | Motion sweep, clearance, moving-part reports | Completed bounded clearance skeleton; FEA/dynamic/sweep deferred | After mechanism DSL and motion-state representation | Reviewer approval |
| `CAD-P09` | First target object end-to-end integration | First kinetic object pipeline from spec to STEP/report | Completed target-object integration; export approval remains required | Final integration phase | Human approval |

Cross-cutting deferral: FEA is intentionally not assigned to any current phase. FEA requires a separate approved safety-analysis phase with solver selection, material model assumptions, mesh-quality criteria, legal/safety framing, and validation evidence.

## 4.1 Functional gap task index

Detailed task plans live under `docs/cadagent_plans/CAD-FG-*/implementation-plan.md`. `TASKS.md` records their current inventory, classification, and completion history.

| Task ID | Task name | Plan | Classification |
|---|---|---|---|
| `CAD-FG-00` | Maintained-doc status drift reconciliation | `docs/cadagent_plans/CAD-FG-00/implementation-plan.md` | `executable_now` |
| `CAD-FG-01` | Active workflow safety gate integration | `docs/cadagent_plans/CAD-FG-01/implementation-plan.md` | `approval_required` |
| `CAD-FG-02` | Validation report and artifact metadata hardening | `docs/cadagent_plans/CAD-FG-02/implementation-plan.md` | `approval_required` |
| `CAD-FG-03` | Model Gateway and data-classification API integration | `docs/cadagent_plans/CAD-FG-03/implementation-plan.md` | `approval_required` |
| `CAD-FG-04` | Agent route hardening decision and implementation | `docs/cadagent_plans/CAD-FG-04/implementation-plan.md` | `approval_required` |
| `CAD-FG-05` | Production infrastructure deferral | `docs/cadagent_plans/CAD-FG-05/implementation-plan.md` | `blocked` |

## 5. Detailed implementation phases

### `CAD-P00` — Source/design contract finalization

**Design coverage**

- Source traceability from Origen CADAGENT proposal to maintained design and plan artifacts.
- Phase gates, stop conditions, review package template, and validation discipline.

**Current status**

- Completed docs-only.

**Implementation goal**

- Maintain implementation contracts that make future CADAGENT work reviewable and bounded.
- Keep Phase 0 contract docs as planning/contract artifacts unless a later approved pass authorizes code.

**Non-goal**

- Do not implement CAD features, API services, worker pools, LLM endpoints, production storage, or production auth in this phase.
- Do not treat contract docs as executable production infrastructure.

**Entry criteria**

- `docs/cad_agent_detailed_design.md` exists.
- `docs/cad_agent_implementation_plan.md` exists.
- Origen source and current repo maturity are reconciled.

**Exit criteria**

- Required contract docs exist and are included in maintained doc validation.
- Phase gates, stop conditions, and review package requirements are explicit.
- Docs avoid stale validation terms.
- `validate-docs` passes.

**Primary files**

- `docs/MVP_SCOPE.md`
- `docs/MECHANISM_DSL_V1.md`
- `docs/CAD_RUNTIME_CONTRACT.md`
- `docs/VALIDATION_CONTRACT.md`
- `docs/ORCHESTRATOR_WORKFLOW.md`
- `src/cad_agent/tools/validate_platform_contracts.py`
- `docs/cad_agent_implementation_plan.md`

**Validation commands**

```bash
bash ./run_cad_agent.sh validate-docs
git diff --check
git diff --check --no-index /dev/null docs/cad_agent_detailed_design.md
git diff --check --no-index /dev/null docs/cad_agent_implementation_plan.md
```

**Gate**

- Reviewer approval.

**Deferred production boundaries**

- No production code, schemas, API endpoints, worker pools, auth, durable storage, or real LLM routes are authorized by this phase.

---

### `CAD-P01` — Native CAD golden path hardening

**Design coverage**

- Deterministic CAD Runtime receives validated DSL.
- STEP / B-Rep are canonical geometry artifacts.
- STL / 3MF / glTF / PNG / PDF are derived artifacts.
- Runtime records success/failure and artifact hashes.
- Export failures are surfaced as structured validation failures.

**Current status**

- Completed/hardened PoC/native CadQuery path.

**Implementation goal**

- Maintain the existing single-part golden CAD path as a bounded PoC/native CadQuery validation path.
- Keep schema/AST, parameter references, z-only axes, `step_ap242`, export failure handling, and artifact/hash metadata checks enforced.

**Non-goal**

- Do not deploy production native CAD workers.
- Do not add arbitrary CAD features outside an approved hardening pass.
- Do not treat deterministic surrogate output as production native CAD proof.
- Do not implement mechanism DSL operations in this phase.

**Entry criteria**

- Phase 0 contract docs exist.
- Existing Phase 1 PoC/native CadQuery path is present.
- Phase 1 validation fixtures are available.

**Exit criteria**

- `phase1-contract-test` passes.
- `phase1-golden-pipeline` passes.
- Parameter reference validation rejects unresolved references.
- Unsupported DSL operations and non-z axes fail validation.
- `derivative_outputs` requires `step_ap242`.
- Export failures are reported as `EXPORT_FAILED`.
- Artifact hashes are recomputed and metadata contains `cad_kernel`.

**Primary files**

- `src/cad_agent/platform_poc.py`
- `src/cad_agent/schema_gate.py`
- `tests/test_platform_poc.py`
- `artifacts/phase1_poc/`
- `docs/CAD_RUNTIME_CONTRACT.md`
- `docs/VALIDATION_CONTRACT.md`

**Validation commands**

```bash
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_phase1_review
uv run pytest -q
git diff --check
```

**Gate**

- Reviewer approval.

**Deferred production boundaries**

- Production native worker deployment, production artifact store, production export service, and mechanism DSL operations remain deferred.

---

### `CAD-P02` — DFM/AM validation pilot

**Design coverage**

- Validation returns machine-readable reason codes.
- Failed artifacts are not exported for print.
- DFM/AM validation applies manufacturing profile rules.
- Audit and model gateway probes preserve route/data-classification evidence.

**Current status**

- Completed Pilot.

**Implementation goal**

- Maintain local DFM/AM Pilot coverage for `fdm_standard`, worker probes, review diff HTML, audit JSONL, and model gateway probes.
- Keep production worker deployment deferred.

**Non-goal**

- Do not deploy production workers, queues, auth, or real LLM endpoints.
- Do not approve print/export solely because the pilot passes.
- Do not replace deterministic surrogate behavior with production manufacturing evidence.

**Entry criteria**

- Phase 1 golden path is available.
- Phase 2 pilot fixtures and profile rules exist.

**Exit criteria**

- `phase2-pilot-run` passes.
- DFM/AM profile checks return pass/fail with reason codes.
- Worker probes record native or surrogate status.
- Review diff HTML artifact is written.
- Audit JSONL includes `data_classification`, `retention_days`, and `model_route`.
- Model Gateway probes cover public commercial, confidential commercial, regulated, and export-controlled routing.

**Primary files**

- `src/cad_agent/phase2_pilot.py`
- `tests/test_phase2_pilot.py`
- `artifacts/phase2_pilot_validation/`
- `docs/VALIDATION_CONTRACT.md`
- `docs/validation_security_ja.md`

**Validation commands**

```bash
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_phase2_review
uv run pytest -q
git diff --check
```

**Gate**

- Reviewer approval.

**Deferred production boundaries**

- Production worker pools, production manufacturing approval, real LLM endpoints, and durable audit storage remain deferred.

---

### `CAD-P03` — Bounded workflow safety gate

**Design coverage**

- Orchestrator controls workflow state, gates, revision loops, and escalation.
- Spec freeze, validation override, spec change, and print/export require approval.
- Three or more validation failures escalate to human review.
- Audit log preserves state transitions and decisions.
- Failed or unapproved artifacts are not exported.

**Current status**

- Completed skeleton; production API/worker/schema scope remains deferred.

**Implementation goal**

- Implement a local in-process workflow safety gate around the existing Phase 1/2 pipeline.
- Enforce spec approval before CAD generation, revision requests after validation failure, export approval before print/export, and escalation after repeated failures.
- Reuse existing Phase 2 audit style rather than inventing production logging.

**Non-goal**

- Do not implement a full production Orchestrator service.
- Do not implement production API/auth/worker/storage.
- Do not integrate real LLM endpoints.
- Do not add mechanism DSL, motion validation, FEA, or production CAD features.
- Do not treat this phase as a production workflow engine.

**Entry criteria**

- Phase 1 golden path passes.
- Phase 2 Pilot passes.
- Existing approval helper/sample records are identified as non-enforcing.
- Reviewer approves this bounded phase.

**Exit criteria**

- Workflow state machine exists locally and records transitions.
- CAD generation is blocked without `specification_freeze` approval.
- Validation failure creates a revision request with reason codes.
- Three validation failures produce `escalated_to_human`.
- Export/print is blocked unless validation passed and export approval exists.
- Validation override requires explicit approval.
- Spec change requires new approval.
- Audit JSONL records state transitions, approvals, rejections, revision requests, and export decisions.
- Tests cover approval bypass prevention and export blocking.

**Primary files**

- New: `src/cad_agent/orchestrator.py`
- New: `tests/test_orchestrator.py`
- Existing: `src/cad_agent/platform_poc.py`
- Existing: `src/cad_agent/phase2_pilot.py`
- Existing: `tests/test_platform_poc.py`
- Existing: `tests/test_phase2_pilot.py`
- Docs: `docs/ORCHESTRATOR_WORKFLOW.md`, `docs/cad_agent_implementation_plan.md`

**Validation commands**

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_orchestrator_phase1
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_orchestrator_phase2
bash ./run_cad_agent.sh serve --dry-run
git diff --check
```

**Gate**

- Human/reviewer approval because this phase changes workflow safety behavior.

**Deferred production boundaries**

- Production API service, auth, durable artifact store, worker queues, real LLM endpoints, production CAD features, full assembly/motion/FEA validation, and PLM/ERP/MES adapters remain deferred.

---

### `CAD-P04` — Local API/project/job/artifact workflow v1

**Design coverage**

- API / infrastructure future work.
- Project Service, job queue, artifact lookup, `/health`, `/metrics`, and synchronous local job simulation.
- Artifact store remains local PoC/Pilot unless later approved.

**Current status**

- Completed local skeleton; production API/auth/worker/storage deployment remains deferred.

**Implementation goal**

- Harden the local API skeleton as an in-process workflow interface after `CAD-P03`.
- Add bounded local routes or job types for workflow run, revision, and export decisions without production deployment.
- Keep project service, job queue, and artifact index deterministic and local.

**Non-goal**

- Do not deploy production API service, auth, worker pool, durable storage, or external queue.
- Do not expose real LLM routes.
- Do not make API skeleton imply production readiness.

**Entry criteria**

- `CAD-P03` workflow safety gate passes.
- Existing `api_server.py`, `project_service.py`, `job_queue.py`, and artifact index behavior are understood.

**Exit criteria**

- Local API routes enforce the workflow safety gate.
- `/health` and `/metrics` remain deterministic.
- Project/job/artifact endpoints are in-memory/local only.
- Export endpoint returns blocked decisions when approval or validation is missing.
- Tests cover local API gate behavior.
- Existing API skeleton smoke test passes with `serve --dry-run`; API integration remains `CAD-P04`.

**Primary files**

- `src/cad_agent/api_server.py`
- `src/cad_agent/project_service.py`
- `src/cad_agent/job_queue.py`
- `src/cad_agent/orchestrator.py`
- `src/cad_agent/observability.py`
- `tests/test_api_server.py`
- `tests/test_orchestrator.py`
- `docs/api_contracts_ja.md`
- `docs/ORCHESTRATOR_WORKFLOW.md`

**Validation commands**

```bash
uv run pytest -q
bash ./run_cad_agent.sh serve --dry-run
bash ./run_cad_agent.sh validate-docs
git diff --check
```

**Gate**

- Reviewer approval.

**Deferred production boundaries**

- Production API/auth/worker/storage, external queue, durable artifact store, real LLM endpoints, and production deployment remain deferred.

---

### `CAD-P05` — Assembly DSL and AABB validation

**Design coverage**

- Assembly validation for part placement and interference.
- AABB interference/separation/adjacency checks.
- Assembly STEP remains future until CAD runtime supports multi-part operations.

**Current status**

- Completed bounded skeleton; full B-Rep/motion/FEA/PLM remains deferred.

**Implementation goal**

- Define and implement a bounded Assembly DSL contract and AABB-based local checks for simple part placement.
- Keep assembly validation separate from mechanism DSL and motion validation.

**Non-goal**

- Do not implement full B-Rep interference validation.
- Do not implement mechanism operations.
- Do not implement production assembly storage or PLM integration.
- Do not treat AABB checks as full geometric assembly validation.

**Entry criteria**

- Phase 1 DSL validation is stable.
- `CAD-P03` approval/export gate is implemented or explicitly approved in parallel.
- Assembly contract is reviewed.

**Exit criteria**

- Approved assembly contract document exists.
- Deterministic AABB interference, separation, and adjacency checks have tests.
- Assembly validation report includes reason codes and failure locations.
- Assembly export is blocked unless validation passes and approval gate is satisfied.

**Primary files**

- `src/cad_agent/assembly_checks.py`
- `src/cad_agent/platform_poc.py`
- `src/cad_agent/orchestrator.py`
- `docs/MECHANISM_DSL_V1.md` or new assembly contract doc
- `tests/test_assembly_checks.py`
- `tests/test_orchestrator.py`

**Validation commands**

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_assembly_phase1
git diff --check
```

**Gate**

- Reviewer approval.

**Deferred production boundaries**

- Full B-Rep interference, production assembly storage, PLM/ERP/MES adapters, motion validation, and FEA remain deferred.

---

### `CAD-P06` — Mechanism DSL and deterministic compiler

**Design coverage**

- Mechanism Planner proposes mechanism structure.
- DSL Compiler converts approved mechanism plan/specification into allowlisted Parametric DSL.
- DSL operations are allowlisted and schema/AST validated.
- New operations require human approval.

**Current status**

- Completed deterministic compiler skeleton; new-operation approval gate implemented.

**Implementation goal**

- Implement deterministic mechanism DSL operations and a bounded Specification/Mechanism Plan to Parametric DSL compiler service.
- Keep the compiler deterministic, allowlisted, schema-validating, and audit-traceable.

**Non-goal**

- Do not add real LLM generation in this phase unless `CAD-P07` is explicitly merged/split by approval.
- Do not add raw code execution.
- Do not implement motion validation or FEA.
- Do not create production material DB or parts library.

**Entry criteria**

- Phase 1 DSL validation is stable.
- Assembly DSL contract or relevant mechanism DSL contract is approved.
- `CAD-P03` approval/export gate is implemented or explicitly approved in parallel.

**Exit criteria**

- Mechanism DSL allowlist is defined.
- Compiler rejects unsupported operations and unresolved parameters.
- Compiler emits Parametric DSL with traceability IDs.
- AST/schema validation passes for golden mechanism fixtures.
- New operation requests require human/reviewer approval.
- Tests cover valid operations, unsupported operations, unresolved parameters, and traceability metadata.

**Primary files**

- `src/cad_agent/dsl_compiler.py` or equivalent new module
- `src/cad_agent/platform_poc.py`
- `src/cad_agent/schema_gate.py`
- `src/cad_agent/orchestrator.py`
- `docs/MECHANISM_DSL_V1.md`
- `tests/test_dsl_compiler.py`
- `tests/test_platform_poc.py`

**Validation commands**

```bash
uv run pytest -q
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh validate-docs
git diff --check
```

**Gate**

- Reviewer approval.

**Deferred production boundaries**

- Real LLM routes, production parts library, production material DB, motion validation, FEA, and raw code execution remain deferred.

---

### `CAD-P07` — LLM agents and schema-retry routes

**Design coverage**

- Requirement Extractor converts human intent into `Requirement JSON`.
- Spec Composer converts requirements into human-reviewable `Specification JSON`.
- Mechanism Planner proposes mechanism structure.
- Model Gateway applies data-classification routing.
- LLM outputs must be schema-valid before downstream use.

**Current status**

- Completed local/mock skeleton; real LLM endpoints and production model infrastructure remain deferred.

**Implementation goal**

- Implement bounded local/mock LLM-agent route functions using approved prompts, schema validation, retry policy, and deterministic fallback/golden fixtures when needed.
- Keep all LLM outputs as structured JSON/DSL proposals only.
- Treat “routes” as bounded function-level or local mock API layer work, not production LLM endpoints.

**Non-goal**

- Do not send confidential, regulated, or export-controlled data to commercial routes without approval.
- Do not allow LLMs to execute raw code or change approved specs alone.
- Do not implement production model infrastructure.
- Do not bypass `CAD-P03` approval/export gate.

**Entry criteria**

- Phase 0 contracts exist.
- `CAD-P03` approval/revision/export gate is implemented.
- Schema retry tests and model routing policy are approved.

**Exit criteria**

- Requirement Extractor route returns schema-valid `Requirement JSON` or structured failure.
- Spec Composer route returns schema-valid `Specification JSON` or structured failure.
- Mechanism Planner route returns schema-valid mechanism plan or structured failure.
- Schema retry policy is deterministic and auditable.
- Commercial/on-prem routing policy is enforced.
- Tests cover valid JSON, invalid JSON retry, max-retry failure, confidential routing, and audit records.

**Primary files**

- `src/cad_agent/agents/requirement_extractor.py` or equivalent
- `src/cad_agent/agents/spec_composer.py` or equivalent
- `src/cad_agent/agents/mechanism_planner.py` or equivalent
- `src/cad_agent/phase2_pilot.py`
- `src/cad_agent/security_policy.py`
- `src/cad_agent/orchestrator.py`
- `tests/test_agents.py`
- `tests/test_security.py`
- `docs/validation_security_ja.md`

**Validation commands**

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_agents_phase2
git diff --check
```

**Gate**

- Human approval for prompt/routing policy and data-classification behavior.

**Deferred production boundaries**

- Production LLM endpoints, production model gateway, confidential commercial exceptions without approval, regulated/export-controlled automation, and raw code execution remain deferred.

---

### `CAD-P08` — Motion validation

**Design coverage**

- Motion validation for moving parts.
- Rotational sweep and clearance checks.
- Motion reports include pass/fail, reason codes, and failure locations.

**Current status**

- Completed bounded clearance skeleton; FEA, production dynamic simulation, and full sweep collision remain deferred.

**Implementation goal**

- Implement bounded motion-state representation and deterministic motion validation for approved mechanism fixtures.
- Keep motion validation separate from FEA and production release.

**Non-goal**

- Do not implement FEA.
- Do not implement production motion simulation.
- Do not treat simplified sweep/clearance checks as full dynamic analysis.
- Do not approve print/export without `CAD-P03` gates.

**Entry criteria**

- Mechanism DSL and compiler from `CAD-P06` are implemented.
- Motion-state representation is approved.
- `CAD-P03` approval/export gate is active.

**Exit criteria**

- Motion validation input schema is defined.
- Rotational sweep and clearance checks return pass/fail with reason codes.
- Motion validation report includes traceability IDs and failure locations.
- Motion validation failures block export unless an approved override exists.
- Tests cover passing clearance, insufficient clearance, invalid motion state, and override rejection without approval.

**Primary files**

- `src/cad_agent/motion_validation.py` or equivalent
- `src/cad_agent/orchestrator.py`
- `src/cad_agent/platform_poc.py`
- `docs/VALIDATION_CONTRACT.md`
- `tests/test_motion_validation.py`
- `tests/test_orchestrator.py`

**Validation commands**

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_motion_phase1
git diff --check
```

**Gate**

- Reviewer approval.

**Deferred production boundaries**

- FEA, production dynamic simulation, production release, and motion validation for unapproved mechanism DSL remain deferred.

---

### `CAD-P09` — First target object end-to-end integration

**Design coverage**

- Produce first kinetic object from approved target spec through requirement, spec, DSL, CAD, validation, approval, and derived artifacts.
- Preserve traceability across prompts, models, specs, DSL, CAD artifacts, validation reports, and approvals.

**Current status**

- Completed target-object integration; production artifact storage and export approval bypass remain deferred.

**Implementation goal**

- Integrate approved prior phases into a deterministic end-to-end pipeline for the first target object, likely `gyro_kinetic_v1`.
- Produce requirement/spec/DSL/STEP-derived artifacts/report package only after all required gates pass.

**Non-goal**

- Do not skip approval/export gates.
- Do not print/export without approval.
- Do not claim production readiness.
- Do not add FEA unless separately approved.

**Entry criteria**

- Required prerequisite phases are completed or explicitly approved as sufficient for the target.
- Target object spec is approved.
- Validation plan for the target is approved.

**Exit criteria**

- Requirement JSON exists and is schema-valid.
- Specification JSON exists and has approval record.
- Parametric DSL exists and passes schema/AST validation.
- CAD Runtime generates STEP/B-Rep or approved PoC surrogate artifacts with metadata.
- Validation Report records pass/fail and reason codes.
- Approval record exists before print/export.
- Audit log preserves traceability across generated artifacts.
- Full validation suite passes.

**Primary files**

- `src/cad_agent/platform_poc.py`
- `src/cad_agent/orchestrator.py`
- `src/cad_agent/api_server.py` if local API integration is included
- `src/cad_agent/phase2_pilot.py`
- `tests/test_platform_poc.py`
- `tests/test_orchestrator.py`
- `tests/test_api_server.py`
- `artifacts/gyro_kinetic_v1/` only if explicitly approved
- `docs/cad_agent_detailed_design.md`
- `docs/cad_agent_implementation_plan.md`

**Validation commands**

```bash
bash ./run_cad_agent.sh status
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_target_phase1
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_target_phase2
bash ./run_cad_agent.sh serve --dry-run
uv run pytest -q
git diff --check
```

**Gate**

- Human approval for target spec, validation plan, and export decision.

**Deferred production boundaries**

- Production release, production artifact store, production API/auth/worker/storage, FEA, PLM/ERP/MES adapters, and unapproved print/export remain deferred.

## 6. Completed bounded implementation records

This section records completed bounded implementation passes. It does not authorize production deployment, production APIs, worker queues, auth, real LLM endpoints, new `schemas/v1/*`, production CAD features, or example artifacts.

### Phase 1 hardening

The bounded Phase 1 hardening pass updated only the existing Phase 1 PoC/native CadQuery golden path and its contracts/tests. It did not implement production deployment, production APIs, worker queues, auth, real LLM endpoints, new DSL operations, or example artifacts.

Implemented hardening:

- CadQuery STEP/STL export failures are returned as structured `EXPORT_FAILED` validation failures.
- Phase 1 AST/schema checks enforce z-only feature axes.
- Parameter reference strings must resolve to numeric parameters.
- `step_ap242` is required in `derivative_outputs`.
- `phase1-contract-test` writes reports to a temporary output directory instead of repository-local `reports/phase1_contract_test.json`.
- Artifact checks recompute `sha256` hashes and verify metadata contains `cad_kernel`.

Validation evidence:

- `phase1-contract-test` passes.
- `phase1-golden-pipeline --output-dir /tmp/cadagent_phase1_review_final` passes.
- `uv run pytest -q` passes.
- `git diff --check` passes.
- Recomputed artifact hashes match stored hashes.
- Metadata records `cad_kernel` as `cadquery_occt` when CadQuery is available.

### Phase 2 Pilot completion

Phase 2 Pilot is implemented and validated as a local PoC/Pilot path. It does not deploy production workers, production queues, auth, or real LLM endpoints.

Implemented Pilot coverage:

- DFM/AM profile catalog and validation for `fdm_standard`, including wall thickness, hole diameter, material support, and build-volume checks.
- FreeCAD/OCCT and Blender mesh/render worker probes with deterministic surrogate fallback when native executables are absent.
- Review diff HTML artifact for parameter comparison.
- Audit JSONL event with `data_classification`, `retention_days`, and `model_route`.
- Model Gateway probes for public commercial, confidential commercial, regulated, and export-controlled routing.

Validation evidence:

- `phase2-pilot-run` passes.
- DFM/AM profile checks pass.
- Worker probes record native or surrogate status.
- Review UI artifact is written.
- Audit and gateway probes pass.
- Full validation in this reconciliation pass records `phase2-pilot-run --output-dir /tmp/cadagent_remaining_final_phase2` as pass.

### Local API/project/material/assembly skeletons

The repository contains local API/project/job/material/BOM/assembly skeletons and stubs. They are not production features.

Implemented skeleton coverage:

- Standard-library HTTP API Gateway skeleton with in-memory Project Service, API-key stub, artifact index lookup only, synchronous job queue simulation, `/health`, and `/metrics`.
- Security and observability skeleton, including `serve --dry-run` and in-process Prometheus-text counters.
- CI/SBOM/provenance skeleton with deterministic local SBOM and provenance commands.
- Static material catalog, BOM aggregation, and axis-aligned bbox assembly interference/separation/adjacency stubs.

Validation evidence:

- `bash ./run_cad_agent.sh status` passes with `aligned`.
- `bash ./run_cad_agent.sh validate-docs` passes.
- `bash ./run_cad_agent.sh phase1-contract-test` passes.
- `bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_remaining_final_phase1` passes.
- `bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_remaining_final_phase2` passes.
- `bash ./run_cad_agent.sh serve --dry-run`, `sbom`, and `provenance` pass.
- `uv run pytest -q` passes.
- `git diff --check` passes.

## 7. Validation commands

### Per phase

```bash
bash ./run_cad_agent.sh status
bash ./run_cad_agent.sh validate-docs
git diff --check
git diff --check --no-index /dev/null docs/cad_agent_detailed_design.md
git diff --check --no-index /dev/null docs/cad_agent_implementation_plan.md
```

### Final gate

```bash
bash ./run_cad_agent.sh status
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline
bash ./run_cad_agent.sh phase2-pilot-run
bash ./run_cad_agent.sh serve --dry-run
bash ./run_cad_agent.sh sbom
bash ./run_cad_agent.sh provenance
uv run pytest -q
git diff --check
```

Review-specific Phase 1/2 validation runs use `/tmp` output directories; the generic command names above are the maintained final gate commands.

## 8. Review package requirements

Each phase review package must include:

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

### Must-fix closure
-

### Deferred should-fix / optional items
-

### Next phase proposal
-
```

Review verdict must be one of:

- `pass`
- `conditional pass`
- `blocked`

## 9. Stop conditions

Stop and submit only the review package if any condition is true:

- Validation fails.
- Review is not approved.
- Must-fix items remain open.
- A phase attempts forbidden implementation work.
- A stale validation term appears in maintained docs.
- A phase attempts to create Phase 0 contract docs outside the approved Phase 0 design-contract finalization pass.
- A phase attempts to imply production readiness for skeleton/stub work.
- A phase attempts FEA, motion validation, production API/auth/worker/storage, real LLM endpoints, or print/export without explicit approval.

## 10. Risk register

| Risk | Mitigation |
|---|---|
| Planning docs are mistaken for implementation | Mark each doc as planning-only and list forbidden work. |
| Completed skeletons are mistaken for production readiness | Keep maturity labels explicit and separate skeleton completion from production deployment. |
| Approval samples are mistaken for enforced gates | Document that approval helpers are audit-shape samples only; implement `CAD-P03` approval/revision/export gates before production export. |
| Old denylists block requested docs | Remove only the exact denylist for approved docs; keep code/contract forbiddance. |
| Future agents create implementation code | Keep validation-harness-only scope and require approval for code phases. |
| New docs diverge from Origen source | Include source-to-plan traceability tables. |
| Stale terms reappear | Run `validate-docs` and avoid stale terms in maintained docs. |
| Full validation is skipped | Require final full validation before closing the pass. |
| FEA is mistaken for current scope | Keep explicit FEA deferral note until a separate safety-analysis phase is approved. |

## 11. Decision log

| ID | Decision | Rationale |
|---|---|---|
| CAD-D001 | Create `docs/cad_agent_detailed_design.md` | User explicitly requested a maintained detailed design document. |
| CAD-D002 | Create `docs/cad_agent_implementation_plan.md` | User explicitly requested a maintained implementation plan document. |
| CAD-D003 | Keep implementation code forbidden in planning passes | Planning passes define gates and scope; code phases require explicit approval. |
| CAD-D004 | Phase 0 contract docs require the approved Phase 0 design-contract finalization pass | Those docs are implementation contracts, not prompt workflow planning docs. |
| CAD-D005 | Add new docs to `validate-docs` | Maintained docs must be required and stale-term scanned. |
| CAD-D006 | Use `gyro_kinetic_v1` instead of stale labels | Avoids stale validation terms while preserving the target concept. |
| CAD-D007 | Treat Phase 1 hardening as bounded PoC/native CadQuery work | Keeps existing validation useful without authorizing production native worker deployment. |
| CAD-D008 | Require `step_ap242` and z-only axes in Phase 1 contracts | Aligns schema and AST validation with the approved single-part golden path. |
| CAD-D009 | Keep contract-test output outside repository reports | Prevents stale ignored report artifacts from polluting review evidence. |
| CAD-D010 | Record Phase 2 and local skeleton completion status | Prevents future agents from re-implementing completed skeleton/Pilot work while preserving production deferrals. |
| CAD-D011 | Rewrite the implementation plan around `CAD-P00`..`CAD-P09` | Makes the plan actionable against `docs/cad_agent_detailed_design.md`. |
| CAD-D012 | Make `CAD-P03` the next implementation phase | Approval/revision/export gate is the highest-value bounded safety phase after Phase 1/2. |

## 12. Definition of done

This plan rewrite is done when:

- `docs/cad_agent_implementation_plan.md` uses the `CAD-P00`..`CAD-P09` structure.
- Every phase states current status, implementation goal, non-goal, entry criteria, exit criteria, primary files, validation, gate, and deferred production boundaries.
- The plan states that the full detailed design is not yet implemented.
- The plan states that `CAD-P03` bounded workflow safety gate is the recommended next implementation phase.
- Phase 1 hardening and Phase 2 Pilot evidence are recorded without implying production readiness.
- Local API/project/material/assembly work is described as skeleton/stub, not production-ready.
- FEA is explicitly deferred until a separate safety-analysis phase is approved.
- `validate-docs` passes.
- Diff checks pass.
- @oracle final review is `pass` or non-blocking `conditional pass`.

# CADAGENT Implementation Plan

## 1. Document status

- Status: maintained implementation planning artifact; Phase 1 hardening record included
- Source: `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`
- Related detailed design: `docs/cad_agent_detailed_design.md`
- Scope boundary: this document defines implementation phases and gates, and records the bounded Phase 1 hardening pass. It does not authorize production CAD features, native workers, schemas, API services, LLM endpoints, or production architecture.

## 2. Scope for this pass and Phase 1 hardening

This document was created in the Phase 0 docs-only pass and later updated to record the bounded Phase 1 hardening pass for the existing PoC/native CadQuery golden path.

The Phase 0 pass created planning documents only, plus the five Phase 0 contract docs when this was the approved Phase 0 design-contract finalization pass. The Phase 1 hardening pass did not deploy production workers, APIs, queues, auth, or real LLM endpoints.

Allowed:

- Create `docs/cad_agent_detailed_design.md`.
- Create `docs/cad_agent_implementation_plan.md`.
- Create or maintain `docs/MVP_SCOPE.md`, `docs/MECHANISM_DSL_V1.md`, `docs/CAD_RUNTIME_CONTRACT.md`, `docs/VALIDATION_CONTRACT.md`, and `docs/ORCHESTRATOR_WORKFLOW.md` only in the approved Phase 0 design-contract finalization pass.
- Update `prompt.md`, `docs/prompt_execution_plan.md`, `TASKS.md`, `docs/operations_ja.md`, and `src/cad_agent/tools/validate_platform_contracts.py`.
- Harden the existing Phase 1 PoC/native CadQuery path when explicitly approved.
- Run validation commands.
- Record prompt-workflow review evidence in `.slim/deepwork/prompt_workflow_framework.md`.
- Record CADAGENT Phase 0 and Phase 1 hardening review evidence in `.slim/deepwork/cadagent-implementation-pass.md` and `.slim/deepwork/cadagent-phase1-implementation.md`.

Forbidden in this pass unless executing the approved Phase 0 design-contract finalization pass:

- Add or update `schemas/v1/*`.
- Add implementation code under `cad_runtime/`, `dsl/`, or `validation/` outside an explicitly approved hardening pass.
- Add native worker pool.
- Add real LLM endpoint integration.
- Add production API service implementation.
- Add CAD feature implementation outside an explicitly approved hardening pass.
- Add `examples/gyro_kinetic_v1/*` artifacts.
- Create Phase 0 contract docs such as `docs/MVP_SCOPE.md`, `MECHANISM_DSL_V1.md`, `CAD_RUNTIME_CONTRACT.md`, `VALIDATION_CONTRACT.md`, or `ORCHESTRATOR_WORKFLOW.md` unless this is the approved Phase 0 design-contract finalization pass; then they are docs-only.

## 3. Current repository maturity

| Area | Current state | Implementation implication |
|---|---|---|
| CLI | Present | Use `run_cad_agent.sh` as the local validation entrypoint. |
| Phase 1 PoC | Present | Requirement, Specification, Parametric DSL, Validation Report contracts are available. |
| Phase 2 Pilot | Present | DFM/AM profile, review diff, audit, and gateway probes are available. |
| Production v1 | Skeleton only | Do not treat as production-ready. |
| Production v2 | Skeleton only | Material/BOM/AABB assembly remains stubbed. |
| Native CAD | Phase 1 PoC/native CadQuery path present and hardened | Use for validation; production native worker deployment remains future work. |
| LLM endpoints | Not integrated | Model Gateway remains policy/probe only. |

## 4. Source-to-plan traceability

| Origen phase | Maintained implementation plan section | Current repo state | Future status |
|---|---|---|---|
| Phase 0: design contract fixation | Section 5 | Phase 0 contract docs maintained by approved finalization pass | Future approved implementation phases |
| Phase 1: native CAD golden path | Sections 5 and 6.1 | PoC/native CadQuery path exists and was hardened | Future native worker implementation |
| Phase 2: DFM validation | Section 5 | Pilot profile checks exist | Strengthen DFM/AM validation |
| Phase 3: Assembly DSL | Section 5 | AABB stubs only | Future assembly DSL |
| Phase 4: Mechanism DSL | Section 5 | Planning only | Future mechanism operations |
| Phase 5: Motion validation | Section 5 | Future concept | Future motion validation |
| Phase 6: LLM agents | Section 5 | Prompt boundaries only | Future LLM endpoint integration |
| Phase 7: Revision loop / approval | Section 5 | Samples/stubs exist | Future workflow implementation |
| Phase 8: first target object | Section 5 | Planning only | Future approved target implementation |

## 5. Immediate docs-only implementation phases

| Phase | Purpose | Inputs | Outputs | Gate | Validation |
|---|---|---|---|---|---|
| `CAD-P00` | Reconcile user correction | User request, Origen source, existing prompt workflow docs | Revised deliverable plan | @oracle review | `validate-docs`, diff checks |
| `CAD-P01` | Create detailed design | Origen source, current repo maturity | `docs/cad_agent_detailed_design.md` | @oracle review | `validate-docs`, no-index diff check |
| `CAD-P02` | Create implementation plan | Origen source phases, current repo maturity | `docs/cad_agent_implementation_plan.md` | @oracle review | `validate-docs`, no-index diff check |
| `CAD-P03` | Update execution references | New docs, existing prompt docs | Updated `prompt.md`, `docs/prompt_execution_plan.md`, `TASKS.md`, `docs/operations_ja.md` | @oracle review | `validate-docs`, diff checks |
| `CAD-P04` | Update validation coverage | New docs, validation script | `src/cad_agent/tools/validate_platform_contracts.py` includes new docs | @oracle review | `validate-docs`, `pytest` |
| `CAD-P05` | Final validation and review package | All changed files | Review package and final summary | @oracle final review | Full validation suite |

## 6. Future approved CADAGENT phases

| Phase | Purpose | Inputs | Outputs | Gate | Validation | Forbidden until approved |
|---|---|---|---|---|---|---|
| Phase 0: design contract finalization | Convert planning into implementation contracts | Approved detailed design | `MVP_SCOPE.md`, `MECHANISM_DSL_V1.md`, `CAD_RUNTIME_CONTRACT.md`, `VALIDATION_CONTRACT.md`, `ORCHESTRATOR_WORKFLOW.md` | Human/reviewer approval | Contract review | Code implementation |
| Phase 1: native CAD golden path | Generate real STEP/B-Rep from validated DSL | Approved CAD Runtime contract | Native CAD worker, STEP/STL export, artifact manifest | Reviewer approval | Phase 1 pipeline, artifact hash checks | Existing PoC/native CadQuery hardening only; production deployment |
| Phase 2: DFM/AM validation | Enforce manufacturing profile rules | Approved validation contract | DFM/AM checks, reason codes, report propagation | Reviewer approval | Phase 2 pilot plus stronger checks | Print export without approval |
| Phase 3: Assembly DSL | Support multi-part placement and constraints | Approved assembly contract | Assembly DSL, AABB/interference checks, assembly STEP | Reviewer approval | Assembly regression tests | Native worker pool |
| Phase 4: Mechanism DSL | Add mechanism operations | Approved mechanism contract | Gear, shaft, bearing, cage, ring operations | Reviewer approval | Mechanism golden tests | Raw code execution |
| Phase 5: Motion validation | Validate moving parts | Approved motion contract | Motion sweep checks, clearance reports | Reviewer approval | Motion regression tests | Production release |
| Phase 6: LLM agent implementation | Generate requirement/spec/DSL from intent | Approved prompts and routes | Requirement Extractor, Spec Composer, Mechanism Planner, DSL Compiler | Human approval | Schema retry tests | Commercial route for confidential data |
| Phase 7: Revision loop / approval | Safe correction and escalation | Approved workflow contract | Revision loop, approval API, audit log | Human approval | State-machine tests | Validation override without approval |
| Phase 8: first target object | Produce first kinetic object | Approved target spec | Requirement, spec, DSL, STEP, derived artifacts, report | Human approval | Full pipeline validation | Print export without approval |

## 6.1 Phase 1 hardening record

The bounded Phase 1 hardening pass updated only the existing Phase 1 PoC/native CadQuery golden path and its contracts/tests. It did not implement production deployment, production APIs, worker queues, auth, real LLM endpoints, new DSL operations, or example artifacts.

Implemented hardening:
- CadQuery STEP/STL export failures are returned as structured `EXPORT_FAILED` validation failures.
- Phase 1 AST/schema checks enforce z-only feature axes.
- Parameter reference strings must resolve to numeric parameters.
- `step_ap242` is required in `derivative_outputs`.
- `phase1-contract-test` writes reports to a temporary output directory instead of `reports/phase1_contract_test.json`.
- Artifact checks recompute `sha256` hashes and verify metadata contains `cad_kernel`.

Validation evidence:
- `phase1-contract-test` passes.
- `phase1-golden-pipeline --output-dir /tmp/cadagent_phase1_review_final` passes.
- `uv run pytest -q` passes.
- `git diff --check` passes.
- Recomputed artifact hashes match stored hashes.
- Metadata records `cad_kernel` as `cadquery_occt` when CadQuery is available.

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
uv run pytest -q
git diff --check
```

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

## 10. Risk register

| Risk | Mitigation |
|---|---|
| Planning docs are mistaken for implementation | Mark each doc as planning-only and list forbidden work. |
| Old denylists block requested docs | Remove only the exact denylist for approved docs; keep code/contract forbiddance. |
| Future agents create implementation code | Keep validation-harness-only scope and require approval for code phases. |
| New docs diverge from Origen source | Include source-to-plan traceability tables. |
| Stale terms reappear | Run `validate-docs` and avoid stale terms in maintained docs. |
| Full validation is skipped | Require final full validation before closing the pass. |

## 11. Decision log

| ID | Decision | Rationale |
|---|---|---|
| CAD-D001 | Create `docs/cad_agent_detailed_design.md` | User explicitly requested a maintained detailed design document. |
| CAD-D002 | Create `docs/cad_agent_implementation_plan.md` | User explicitly requested a maintained implementation plan document. |
| CAD-D003 | Keep implementation code forbidden in this pass | The request is for planning artifacts, not CAD feature implementation. |
| CAD-D004 | Phase 0 contract docs require the approved Phase 0 design-contract finalization pass | Those docs are implementation contracts, not prompt workflow planning docs. |
| CAD-D005 | Add new docs to `validate-docs` | Maintained docs must be required and stale-term scanned. |
| CAD-D006 | Use `gyro_kinetic_v1` instead of stale labels | Avoids stale validation terms while preserving the target concept. |
| CAD-D007 | Treat Phase 1 hardening as bounded PoC/native CadQuery work | Keeps existing validation useful without authorizing production native worker deployment. |
| CAD-D008 | Require `step_ap242` and z-only axes in Phase 1 contracts | Aligns schema and AST validation with the approved single-part golden path. |
| CAD-D009 | Keep contract-test output outside repository reports | Prevents stale ignored report artifacts from polluting review evidence. |

## 12. Definition of done

This pass is done when:

- `docs/cad_agent_detailed_design.md` exists.
- `docs/cad_agent_implementation_plan.md` exists.
- `prompt.md` references both docs.
- `docs/prompt_execution_plan.md` references both docs and no longer forbids them.
- `TASKS.md` and `docs/operations_ja.md` reference the new planning artifacts.
- `src/cad_agent/tools/validate_platform_contracts.py` includes the new docs.
- Phase 1 hardening evidence is recorded in Section 6.1.
- `validate-docs` passes.
- Diff checks pass.
- Full validation suite passes.
- @oracle final review is `pass` or non-blocking `conditional pass`.
- Review evidence is recorded in `.slim/deepwork/prompt_workflow_framework.md` for the prompt workflow pass and `.slim/deepwork/cadagent-implementation-pass.md` for the CADAGENT Phase 0 pass.

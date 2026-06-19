# CAD-P00 — Source/design contract finalization Implementation Plan

> **For agentic workers:** Use this plan task-by-task. Keep this phase docs/contract-only unless a later approval explicitly authorizes code.

**Goal:** Maintain the CADAGENT design-contract baseline so every future implementation phase has approved scope, gates, and traceability.

**Architecture:** This phase keeps source/design contracts in `docs/` and validates them through `src/cad_agent/tools/validate_platform_contracts.py`. It does not add runtime features.

**Tech Stack:** Markdown, Python validation harness, `run_cad_agent.sh`.

## Global Constraints

- Do not implement CAD features, API services, worker pools, LLM endpoints, production storage, production auth, or `schemas/v1/*`.
- Do not treat contract documents as executable production infrastructure.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Completed docs-only baseline.
- Future work in this phase is maintenance only unless a reviewer explicitly reopens it.

## Tasks

### Task 00.1 — Maintain source/design contract documents

**Files:**
- Modify as needed: `docs/MVP_SCOPE.md`, `docs/MECHANISM_DSL_V1.md`, `docs/CAD_RUNTIME_CONTRACT.md`, `docs/VALIDATION_CONTRACT.md`, `docs/ORCHESTRATOR_WORKFLOW.md`
- Test: `bash ./run_cad_agent.sh validate-docs`

**Interfaces:**
- Consumes: Origen source, current design, current implementation plan.
- Produces: maintained contract documents and validation evidence.

- [ ] **Step 1: Read the source contracts**
  - Read `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`.
  - Read `docs/cad_agent_detailed_design.md`.
  - Read `docs/cad_agent_implementation_plan.md`.

- [ ] **Step 2: Check contract coverage**
  - Confirm each contract document still covers scope, non-goals, gates, validation, and approval boundaries.

- [ ] **Step 3: Update only contract wording if needed**
  - Example allowed edit:
    ```markdown
    - Production worker deployment remains deferred until an explicitly approved phase authorizes it.
    ```

- [ ] **Step 4: Run validation**
  ```bash
  bash ./run_cad_agent.sh validate-docs
  git diff --check
  ```

- [ ] **Step 5: Record progress**
  - Update `TASKS.md` under `CAD-P00` with status, validation command IDs, and deviation verdict.

### Task 00.2 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`
- Test: `bash ./run_cad_agent.sh validate-docs`

- [ ] **Step 1: Verify no forbidden code changed**
  ```bash
  git status --short -- cad_runtime dsl validation schemas/v1 examples/gyro_kinetic_v1
  ```
  Expected: no output unless a later approval explicitly authorizes code.

- [ ] **Step 2: Verify plan alignment**
  - Confirm no maintained doc contradicts `docs/cad_agent_detailed_design.md:8` or `docs/cad_agent_implementation_plan.md:8`.

- [ ] **Step 3: Mark complete only if validation passes**
  - Update `TASKS.md` with `CAD-P00` complete, validation result, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P00` complete:

- `validate-docs` passes.
- `git diff --check` passes.
- No production code, API, worker, auth, storage, LLM endpoint, or schema implementation was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
bash ./run_cad_agent.sh validate-docs
git diff --check
git diff --check --no-index /dev/null docs/cad_agent_detailed_design.md
git diff --check --no-index /dev/null docs/cad_agent_implementation_plan.md
```

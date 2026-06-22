# CAD-FG-00 — Maintained-doc status drift reconciliation Implementation Plan

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Reconcile maintained documentation so completed skeleton/Pilot phases are not reworked and completed code is not misrepresented as production-ready.

**Architecture:** Docs/status-only update. No source code, schemas, API endpoints, CAD features, worker deployment, or LLM endpoints.

**Tech Stack:** Markdown, `validate-docs`, `git diff --check`.

## Global Constraints

- Do not edit source code.
- Do not add or modify `schemas/v1/*`.
- Do not add API endpoints, CAD features, worker deployment, or LLM endpoints.
- Do not change approval boundaries.
- Every completion must be recorded in `TASKS.md` only after validation passes.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.
- Classification: `executable_now`.

## Tasks

### Task 00.1 — Update CADAGENT implementation plan status language

**Files:**
- Modify: `docs/cad_agent_implementation_plan.md`

- [ ] **Step 1: Find stale status language**
  - Search for completed phases still described as `Not started`, `Skeleton`, `Stub`, or equivalent stale wording where code/tests/artifacts exist.

- [ ] **Step 2: Update status wording**
  - Mark completed skeleton/Pilot phases as validated skeleton/Pilot maturity.
  - Keep production deployment, real worker pools, real LLM endpoints, FEA, and production artifact storage deferred.

- [ ] **Step 3: Preserve phase boundaries**
  - Do not rewrite completed phases into a production-readiness claim.

### Task 00.2 — Update orchestrator workflow implementation status

**Files:**
- Modify: `docs/ORCHESTRATOR_WORKFLOW.md`

- [ ] **Step 1: Find stale implementation status**
  - Search for wording such as `No implementation` where workflow state-machine code/tests exist.

- [ ] **Step 2: Update implementation status**
  - State that local/in-process workflow safety gates are implemented and validated.
  - Keep production worker/API/auth/storage deployment deferred.

### Task 00.3 — Validate docs-only changes

- [ ] **Step 1: Run docs validation**
  ```bash
  bash ./run_cad_agent.sh validate-docs
  ```

- [ ] **Step 2: Run whitespace check**
  ```bash
  git diff --check
  ```

### Task 00.4 — Record completion evidence

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Update `TASKS.md`**
  - Mark `CAD-FG-00` complete only after validation passes.
  - Record validation commands and deviation-check verdict.

## Completion Deviation Check

Before marking `CAD-FG-00` complete:

- `docs/cad_agent_implementation_plan.md` no longer misrepresents completed skeleton/Pilot phases.
- `docs/ORCHESTRATOR_WORKFLOW.md` no longer says workflow implementation is absent where local implementation exists.
- Production readiness is not claimed.
- No code, schema, API endpoint, CAD feature, worker deployment, or LLM endpoint was added.
- `validate-docs` and `git diff --check` pass.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
bash ./run_cad_agent.sh validate-docs
git diff --check
```

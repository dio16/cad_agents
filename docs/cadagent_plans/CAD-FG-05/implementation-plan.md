# CAD-FG-05 — Production infrastructure deferral Implementation Plan

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Keep production infrastructure deferred until separately approved, while documenting the deferral boundary clearly.

**Architecture:** Docs/status-only update. No production deployment, worker pool, auth, artifact store, or production API service implementation.

**Tech Stack:** Markdown, `validate-docs`, `git diff --check`.

## Global Constraints

- Do not add Kubernetes manifests.
- Do not add KServe/vLLM deployment.
- Do not add Argo CD.
- Do not add Cosign/Trivy production enforcement.
- Do not add production worker pools, production artifact storage, production auth, or production API deployment.
- Every completion must be recorded in `TASKS.md` only after validation passes.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.
- Classification: `blocked` until explicit production-architecture approval.
- Docs/status reconciliation may proceed without production-architecture approval.

## Tasks

### Task 05.1 — Document deferred production infrastructure

**Files:**
- Modify: `docs/cad_agent_implementation_plan.md`
- Modify: `docs/ORCHESTRATOR_WORKFLOW.md` if needed

- [ ] **Step 1: Identify deferred production items**
  - Async job queue.
  - Durable artifact store.
  - Auth.
  - Export worker.
  - Production API/service architecture.
  - Kubernetes, KServe/vLLM, Argo CD, Cosign/Trivy.

- [ ] **Step 2: Update docs**
  - State that these are deferred until a separate production phase is approved.
  - Keep current local/Pilot/skeleton maturity explicit.

### Task 05.2 — Validate docs-only changes

- [ ] **Step 1: Run docs validation**
  ```bash
  bash ./run_cad_agent.sh validate-docs
  ```

- [ ] **Step 2: Run whitespace check**
  ```bash
  git diff --check
  ```

### Task 05.3 — Record completion evidence

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Update `TASKS.md`**
  - Mark `CAD-FG-05` complete only if the approved scope is docs/status reconciliation.
  - If production implementation is requested, keep the task blocked until explicit approval is granted.

## Completion Deviation Check

Before marking `CAD-FG-05` complete:

- Production infrastructure remains deferred unless explicitly approved.
- Docs clearly separate local/Pilot/skeleton from production deployment.
- No production infrastructure files were added.
- `validate-docs` and `git diff --check` pass.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
bash ./run_cad_agent.sh validate-docs
git diff --check
```

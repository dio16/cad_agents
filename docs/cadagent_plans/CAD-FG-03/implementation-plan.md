# CAD-FG-03 — Model Gateway and data-classification API integration Implementation Plan

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Integrate data classification and model routing enforcement into local API/project/agent flows.

**Architecture:** Validate project `data_classification`, enforce commercial/on-prem routing policy, and keep confidential/regulated/export-controlled data off commercial routes.

**Tech Stack:** Python, pytest, local API server, `security_policy.py`, Phase 2 pilot routing policy.

## Global Constraints

- Do not call external LLM endpoints without explicit approval.
- Do not deploy production API/auth/worker/storage.
- Do not weaken existing commercial/on-prem policy.
- Do not add new `schemas/v1/*` unless explicitly approved.
- Every completion must be recorded in `TASKS.md` only after validation passes.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.
- Classification: `approval_required`.

## Tasks

### Task 03.1 — Validate project data classification

**Files:**
- Modify: `src/cad_agent/project_service.py`
- Modify: `tests/test_api_server.py`

- [ ] **Step 1: Write failing test for invalid classification**
  - Project creation/update must reject unknown `data_classification`.

- [ ] **Step 2: Implement validation**
  - Allowed classes should match existing security policy.

### Task 03.2 — Enforce model route policy in API/project flows

**Files:**
- Modify: `src/cad_agent/api_server.py`
- Modify: `src/cad_agent/security_policy.py`
- Modify: `src/cad_agent/phase2_pilot.py`
- Modify: `tests/test_api_server.py`
- Modify: `tests/test_security.py`

- [ ] **Step 1: Write failing tests for route decisions**
  - Public commercial route is allowed.
  - Confidential commercial route is rejected or forced to on-prem.
  - Regulated/export-controlled commercial route is rejected.

- [ ] **Step 2: Integrate route decision**
  - API/project flow should call the existing model routing policy.

### Task 03.3 — Preserve audit evidence

**Files:**
- Modify: `src/cad_agent/api_server.py`
- Modify: `src/cad_agent/phase2_pilot.py`
- Modify: tests

- [ ] **Step 1: Add regression coverage**
  - Audit records must include data classification and model routing decision where applicable.

### Task 03.4 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Run targeted tests**
  ```bash
  uv run pytest tests/test_security.py tests/test_api_server.py -q
  ```

- [ ] **Step 2: Run full validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh serve --dry-run
  git diff --check
  ```

- [ ] **Step 3: Verify forbidden scope**
  ```bash
  git status --short -- schemas/v1 .github k8s docker-compose.yml Dockerfile
  ```

- [ ] **Step 4: Record final verdict**
  - Update `TASKS.md` with validation commands, reviewer verdict, and deviation-check verdict.

## Completion Deviation Check

Before marking `CAD-FG-03` complete:

- Project `data_classification` is validated against allowed classes.
- Requirement/Specification/API flows enforce commercial/on-prem route policy.
- Confidential, regulated, and export-controlled data cannot use commercial routes.
- Audit records preserve route/data-classification evidence where applicable.
- No external LLM endpoint was called.
- No production deployment was added.
- Full validation suite passes.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest tests/test_security.py tests/test_api_server.py -q
uv run pytest -q
bash ./run_cad_agent.sh serve --dry-run
git diff --check
```

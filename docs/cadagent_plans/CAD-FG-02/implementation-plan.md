# CAD-FG-02 — Validation report and artifact metadata hardening Implementation Plan

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Make Validation Reports and artifact metadata enforce the design contract more precisely.

**Architecture:** Add machine-readable `revision_feedback` to failed reports and require metadata `cad_kernel` during artifact/hash provenance checks.

**Tech Stack:** Python, pytest, Phase 1 contract tests, existing artifact metadata.

## Global Constraints

- Do not expand CAD feature scope.
- Do not add production artifact storage.
- Do not change approval boundaries.
- Do not add new `schemas/v1/*` unless explicitly approved.
- Every completion must be recorded in `TASKS.md` only after validation passes.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.
- Classification: `approval_required`.

## Tasks

### Task 02.1 — Define failed-report revision feedback contract

**Files:**
- Modify: `tests/test_platform_poc.py`
- Modify: Phase 1 validation report tests as needed

- [ ] **Step 1: Write failing test for failed report feedback**
  - Failed Validation Report must include `revision_feedback`.

- [ ] **Step 2: Define feedback fields**
  - Include reason codes, failed checks, suggested revision action, and traceability link where available.

### Task 02.2 — Add `revision_feedback` to failed Validation Reports

**Files:**
- Modify: `src/cad_agent/platform_poc.py`
- Modify: tests from Task 02.1

- [ ] **Step 1: Implement feedback adapter**
  - Convert validation failures into deterministic `revision_feedback`.

- [ ] **Step 2: Preserve pass reports**
  - Passing reports should not gain misleading failure feedback.

### Task 02.3 — Validate metadata `cad_kernel`

**Files:**
- Modify: `src/cad_agent/platform_poc.py`
- Modify: `tests/test_platform_poc.py`

- [ ] **Step 1: Write failing metadata test**
  - Metadata must contain `cad_kernel`.

- [ ] **Step 2: Add validation check**
  - Report missing metadata or missing `cad_kernel` as a validation/artifact provenance failure.

### Task 02.4 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Run contract tests**
  ```bash
  bash ./run_cad_agent.sh phase1-contract-test
  ```

- [ ] **Step 2: Run targeted and full tests**
  ```bash
  uv run pytest tests/test_platform_poc.py -q
  uv run pytest -q
  ```

- [ ] **Step 3: Run whitespace check**
  ```bash
  git diff --check
  ```

- [ ] **Step 4: Record final verdict**
  - Update `TASKS.md` with validation commands, reviewer verdict, and deviation-check verdict.

## Completion Deviation Check

Before marking `CAD-FG-02` complete:

- Failed Validation Reports include machine-readable `revision_feedback`.
- Metadata `cad_kernel` is required and validated.
- Artifact/hash provenance tests assert metadata exists, contains `cad_kernel`, and hash records remain valid.
- No production artifact storage was added.
- No new CAD feature was added.
- Full validation suite passes.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
bash ./run_cad_agent.sh phase1-contract-test
uv run pytest tests/test_platform_poc.py -q
uv run pytest -q
git diff --check
```

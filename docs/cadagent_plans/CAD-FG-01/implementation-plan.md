# CAD-FG-01 — Active workflow safety gate integration Implementation Plan

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Enforce Specification approval, Validation pass, and Export approval on the active CAD/API paths.

**Architecture:** Route active golden/API CAD jobs through the deterministic `Workflow` state machine and make export approval verify real validation/artifact state.

**Tech Stack:** Python, pytest, existing Phase 1/2 pipeline, JSONL audit, `run_cad_agent.sh`.

## Global Constraints

- Do not deploy production API/auth/worker/storage.
- Do not add real LLM endpoints.
- Do not add new `schemas/v1/*` without explicit approval.
- Do not add new CAD features or example artifacts.
- Do not bypass validation or approval gates.
- Every completion must be recorded in `TASKS.md` only after validation passes.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.
- Classification: `approval_required`.

## Tasks

### Task 01.1 — Add regression tests for active-path gates

**Files:**
- Modify: `tests/test_platform_poc.py`
- Modify: `tests/test_api_server.py`
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test for CAD without spec approval**
  - Golden/API CAD path must return `SPEC_APPROVAL_REQUIRED` or equivalent blocked decision before CAD generation.

- [ ] **Step 2: Write failing test for artifact storage before validation pass**
  - Artifact store must not persist CAD artifacts unless validation passed.

- [ ] **Step 3: Write failing test for export approval**
  - Export approval must verify real validation/artifact state, not only an in-memory flag.

### Task 01.2 — Route golden pipeline CAD generation through `Workflow`

**Files:**
- Modify: `src/cad_agent/platform_poc.py`
- Modify: `src/cad_agent/orchestrator.py`
- Modify: `tests/test_platform_poc.py`

- [ ] **Step 1: Identify active CAD entrypoint**
  - Locate the golden pipeline function that currently performs CAD generation.

- [ ] **Step 2: Add approval gate**
  - Block CAD generation unless `spec_approved` is true.

- [ ] **Step 3: Preserve deterministic behavior**
  - Keep existing PoC/native CadQuery behavior when gates pass.

### Task 01.3 — Route API CAD jobs through `Workflow`

**Files:**
- Modify: `src/cad_agent/api_server.py`
- Modify: `src/cad_agent/job_queue.py`
- Modify: `tests/test_api_server.py`

- [ ] **Step 1: Identify API job execution path**
  - Locate where local API jobs call CAD/golden pipeline functions.

- [ ] **Step 2: Apply workflow gate**
  - Use the same `Workflow` state machine as orchestrator tests.

- [ ] **Step 3: Preserve local API compatibility**
  - Return deterministic blocked decisions with reason codes when gates fail.

### Task 01.4 — Store artifacts only after validation pass

**Files:**
- Modify: `src/cad_agent/platform_poc.py`
- Modify: `src/cad_agent/api_server.py`
- Modify: `tests/test_platform_poc.py`
- Modify: `tests/test_api_server.py`

- [ ] **Step 1: Add validation-state check before artifact persistence**
  - Artifact storage must require validation pass.

- [ ] **Step 2: Add blocked path tests**
  - If validation failed, CAD artifacts may be generated transiently but must not be stored as accepted artifacts.

### Task 01.5 — Enforce export approval against real state

**Files:**
- Modify: `src/cad_agent/orchestrator.py`
- Modify: `src/cad_agent/api_server.py`
- Modify: `tests/test_orchestrator.py`
- Modify: `tests/test_api_server.py`

- [ ] **Step 1: Remove or restrict `mark_validation_passed()` bypass**
  - Tests must exercise real validation pass state where possible.

- [ ] **Step 2: Require validation and artifact evidence**
  - Export approval must check validation pass and artifact evidence before moving to `exported`.

### Task 01.6 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Run targeted tests**
  ```bash
  uv run pytest tests/test_orchestrator.py tests/test_api_server.py tests/test_platform_poc.py -q
  ```

- [ ] **Step 2: Run full validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_fg01_phase1
  bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_fg01_phase2
  git diff --check
  ```

- [ ] **Step 3: Verify forbidden scope**
  ```bash
  git status --short -- schemas/v1 cad_runtime dsl .github k8s docker-compose.yml Dockerfile
  ```

- [ ] **Step 4: Record final verdict**
  - Update `TASKS.md` with validation commands, reviewer verdict, and deviation-check verdict.

## Completion Deviation Check

Before marking `CAD-FG-01` complete:

- CAD generation is blocked before `spec_approved`.
- Golden/API CAD jobs use the same `Workflow` state machine used by tests.
- Artifacts are stored only after validation pass.
- Export approval verifies real validation/artifact state.
- `mark_validation_passed()` bypass behavior is removed or explicitly restricted.
- No production API/auth/worker/storage deployment was added.
- No real LLM endpoint or new CAD feature was added.
- Full validation suite passes.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest tests/test_orchestrator.py tests/test_api_server.py tests/test_platform_poc.py -q
uv run pytest -q
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_fg01_phase1
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_fg01_phase2
git diff --check
```

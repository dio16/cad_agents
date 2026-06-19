# CAD-P01 — Native CAD golden path hardening Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This phase maintains/hardens the existing single-part PoC/native CadQuery path only.

**Goal:** Keep the existing Phase 1 golden CAD path deterministic, validated, and non-production.

**Architecture:** The phase uses `src/cad_agent/platform_poc.py` as the existing golden pipeline, `schema_gate.py` for schema/AST checks, and Phase 1 fixtures as regression evidence.

**Tech Stack:** Python, CadQuery when available, deterministic surrogate fallback, pytest, local artifact hashing.

## Global Constraints

- Do not deploy production native CAD workers.
- Do not add arbitrary CAD features outside an approved hardening pass.
- Do not treat deterministic surrogate output as production native CAD proof.
- Do not implement mechanism DSL operations in this phase.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Completed/hardened PoC/native CadQuery path.
- Future work in this phase is maintenance/hardening only unless a reviewer explicitly reopens it.

## Tasks

### Task 01.1 — Enforce Phase 1 schema/AST contract

**Files:**
- Modify as needed: `src/cad_agent/schema_gate.py`, `src/cad_agent/platform_poc.py`
- Test: `tests/test_platform_poc.py`

**Interfaces:**
- Consumes: Phase 1 Parametric DSL JSON.
- Produces: pass/fail validation results with reason codes.

- [ ] **Step 1: Write failing test for unresolved parameter reference**
  ```python
  def test_unresolved_parameter_reference_fails():
      dsl = {"parameters": {"outer_diameter": 20}, "features": [{"op": "cylinder", "height": "$missing"}]}
      result = validate_dsl(dsl)
      assert not result.passed
      assert "INVALID_PARAMETER_REFERENCE" in result.reason_codes
  ```

- [ ] **Step 2: Implement minimal validation**
  - Resolve parameter references against numeric parameters.
  - Return `INVALID_PARAMETER_REFERENCE` when unresolved.

- [ ] **Step 3: Add non-z axis regression**
  ```python
  def test_non_z_axis_fails():
      dsl = {"features": [{"op": "cylinder", "axis": "x"}]}
      result = validate_dsl(dsl)
      assert not result.passed
      assert "NON_Z_AXIS" in result.reason_codes
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_platform_poc.py -q
  ```

### Task 01.2 — Enforce derivative output and export failure behavior

**Files:**
- Modify as needed: `src/cad_agent/platform_poc.py`
- Test: `tests/test_platform_poc.py`

- [ ] **Step 1: Write failing test for missing `step_ap242`**
  ```python
  def test_missing_step_ap242_fails():
      dsl = {"derivative_outputs": ["stl"]}
      result = validate_dsl(dsl)
      assert not result.passed
      assert "MISSING_STEP_AP242" in result.reason_codes
  ```

- [ ] **Step 2: Implement minimal validation**
  - Require `step_ap242` in `derivative_outputs`.

- [ ] **Step 3: Write failing test for export failure propagation**
  ```python
  def test_export_failure_is_reported():
      result = run_golden_pipeline(simulate_export_failure=True)
      assert result.validation_report.overall == "fail"
      assert "EXPORT_FAILED" in result.validation_report.reason_codes
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_platform_poc.py -q
  ```

### Task 01.3 — Verify artifact hash and metadata

**Files:**
- Modify as needed: `src/cad_agent/platform_poc.py`, `artifacts/phase1_poc/`
- Test: `tests/test_platform_poc.py`

- [ ] **Step 1: Write failing test for metadata cad_kernel**
  ```python
  def test_artifact_metadata_has_cad_kernel():
      metadata = load_phase1_metadata()
      assert metadata["cad_kernel"] in {"cadquery_occt", "deterministic_surrogate"}
  ```

- [ ] **Step 2: Implement hash recomputation**
  - Recompute `sha256` for stored artifacts.
  - Compare against metadata.

- [ ] **Step 3: Run Phase 1 validation**
  ```bash
  bash ./run_cad_agent.sh phase1-contract-test
  bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_phase1_review
  ```

### Task 01.4 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`
- Test: `uv run pytest -q`, `git diff --check`

- [ ] **Step 1: Verify no mechanism DSL or production worker was added**
  ```bash
  git status --short -- dsl cad_runtime schemas/v1
  ```
  Expected: no new production code outside approved hardening files.

- [ ] **Step 2: Verify plan alignment**
  - Confirm no output claims production native worker deployment.
  - Confirm surrogate/native mode remains explicit.

- [ ] **Step 3: Record final evidence**
  - Update `TASKS.md` with validation commands, pass/fail status, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P01` complete:

- `phase1-contract-test` passes.
- `phase1-golden-pipeline` passes.
- `uv run pytest -q` passes.
- `git diff --check` passes.
- No production worker, production API, mechanism DSL, or production CAD feature was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_phase1_review
uv run pytest -q
git diff --check
```

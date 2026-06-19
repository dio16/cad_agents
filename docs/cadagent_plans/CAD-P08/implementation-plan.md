# CAD-P08 — Motion validation Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This phase implements bounded motion-state representation and deterministic motion validation only. It does not implement FEA or production dynamic simulation.

**Goal:** Implement bounded motion validation for approved mechanism fixtures.

**Architecture:** Add `src/cad_agent/motion_validation.py` that consumes mechanism motion state and returns pass/fail with reason codes. Results flow through the `CAD-P03` workflow gate.

**Tech Stack:** Python, pytest, deterministic geometry proxies, JSON reports.

## Global Constraints

- Do not implement FEA.
- Do not implement production motion simulation.
- Do not treat simplified sweep/clearance checks as full dynamic analysis.
- Do not approve print/export without `CAD-P03` gates.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.

## Tasks

### Task 08.1 — Define motion validation input schema

**Files:**
- Create: `docs/MOTION_VALIDATION_CONTRACT.md`
- Create: `tests/test_motion_validation.py`

**Interfaces:**
- Consumes: mechanism motion state JSON.
- Produces: motion validation report JSON.

- [ ] **Step 1: Write failing test for missing rotation axis**
  ```python
  def test_missing_rotation_axis_fails():
      result = validate_motion({"parts": []})
      assert result.valid is False
      assert result.reason_code == "MISSING_ROTATION_AXIS"
  ```

- [ ] **Step 2: Implement schema check**
  - Require rotation axis, angular range, and moving part IDs.

- [ ] **Step 3: Run test**
  ```bash
  uv run pytest tests/test_motion_validation.py::test_missing_rotation_axis_fails -q
  ```

### Task 08.2 — Implement clearance check

**Files:**
- Create: `src/cad_agent/motion_validation.py`
- Modify: `tests/test_motion_validation.py`

- [ ] **Step 1: Write failing test for insufficient clearance**
  ```python
  def test_insufficient_clearance_fails():
      state = {"rotation_axis": "z", "clearance_mm": 0.2, "min_clearance_mm": 1.0}
      result = validate_motion(state)
      assert result.valid is False
      assert result.reason_code == "INSUFFICIENT_CLEARANCE"
  ```

- [ ] **Step 2: Implement clearance rule**
  - Return `INSUFFICIENT_CLEARANCE` when clearance is below minimum.

- [ ] **Step 3: Add passing case**
  ```python
  def test_sufficient_clearance_passes():
      state = {"rotation_axis": "z", "clearance_mm": 2.0, "min_clearance_mm": 1.0}
      result = validate_motion(state)
      assert result.valid is True
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_motion_validation.py -q
  ```

### Task 08.3 — Produce motion validation report

**Files:**
- Modify: `src/cad_agent/motion_validation.py`
- Modify: `tests/test_motion_validation.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_motion_report_contains_reason_codes():
      result = validate_motion({"rotation_axis": "z", "clearance_mm": 0.2, "min_clearance_mm": 1.0})
      assert result.report["reason_codes"] == ["INSUFFICIENT_CLEARANCE"]
      assert result.report["overall"] == "fail"
  ```

- [ ] **Step 2: Implement report shape**
  - Include traceability ID, pass/fail, reason codes, failure locations, and revision feedback.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_motion_validation.py -q
  ```

### Task 08.4 — Connect motion failure to export gate

**Files:**
- Modify: `src/cad_agent/motion_validation.py`, `src/cad_agent/orchestrator.py`
- Modify: `tests/test_motion_validation.py`, `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_motion_failure_blocks_export():
      workflow = Workflow()
      workflow.handle_motion_validation({"valid": False, "reason_codes": ["INSUFFICIENT_CLEARANCE"]})
      result = workflow.request_export()
      assert result.blocked is True
  ```

- [ ] **Step 2: Implement gate connection**
  - Motion validation failure must keep workflow in `validation_failed` or `revision_requested`.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_motion_validation.py tests/test_orchestrator.py -q
  ```

### Task 08.5 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Verify no FEA or production dynamic simulation was added**
  ```bash
  git diff -- src/cad_agent/motion_validation.py
  ```

- [ ] **Step 2: Run required validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh validate-docs
  bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_motion_phase1
  git diff --check
  ```

- [ ] **Step 3: Record final verdict**
  - Update `TASKS.md` with status, validation commands, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P08` complete:

- Motion validation input schema is defined.
- Rotational sweep and clearance checks return pass/fail with reason codes.
- Motion validation report includes traceability IDs and failure locations.
- Motion validation failures block export unless an approved override exists.
- Tests cover passing clearance, insufficient clearance, invalid motion state, and override rejection without approval.
- No FEA, production dynamic simulation, production release, or motion validation for unapproved mechanism DSL was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_motion_phase1
git diff --check
```

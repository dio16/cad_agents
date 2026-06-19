# CAD-P05 — Assembly DSL and AABB validation Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This phase implements bounded Assembly DSL and AABB checks only. It is not full B-Rep assembly validation.

**Goal:** Define and implement a bounded Assembly DSL contract and deterministic AABB-based local checks for simple part placement.

**Architecture:** Add deterministic assembly validation around existing `assembly_checks.py` and connect results to the `CAD-P03` workflow gate.

**Tech Stack:** Python, pytest, JSON contracts, AABB math.

## Global Constraints

- Do not implement full B-Rep interference validation.
- Do not implement mechanism operations.
- Do not implement production assembly storage or PLM integration.
- Do not treat AABB checks as full geometric assembly validation.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Stub.

## Tasks

### Task 05.1 — Create approved assembly contract document

**Files:**
- Create: `docs/ASSEMBLY_DSL_CONTRACT.md`
- Modify: `docs/cad_agent_implementation_plan.md` only if needed
- Test: `bash ./run_cad_agent.sh validate-docs`

**Interfaces:**
- Consumes: Phase 1 DSL contract and current assembly stubs.
- Produces: reviewed assembly contract.

- [ ] **Step 1: Draft contract**
  ```markdown
  # Assembly DSL Contract

  ## Scope
  - Simple part placement.
  - Axis-aligned bounding boxes.
  - Interference, separation, and adjacency checks.

  ## Non-goals
  - Full B-Rep interference.
  - Motion validation.
  - FEA.
  - Production PLM integration.
  ```

- [ ] **Step 2: Run doc validation**
  ```bash
  bash ./run_cad_agent.sh validate-docs
  ```

- [ ] **Step 3: Record reviewer approval**
  - Add `CAD-P05` contract approval entry to `TASKS.md`.

### Task 05.2 — Implement AABB interference check

**Files:**
- Modify: `src/cad_agent/assembly_checks.py`
- Create: `tests/test_assembly_checks.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_overlapping_aabbs_interfere():
      a = {"min": [0, 0, 0], "max": [10, 10, 10]}
      b = {"min": [5, 5, 5], "max": [15, 15, 15]}
      result = check_interference(a, b)
      assert result.interferes is True
      assert result.reason_code == "AABB_INTERFERENCE"
  ```

- [ ] **Step 2: Implement minimal AABB intersection**
  - Return `AABB_INTERFERENCE` when boxes overlap on all axes.

- [ ] **Step 3: Add separation test**
  ```python
  def test_separated_aabbs_do_not_interfere():
      a = {"min": [0, 0, 0], "max": [10, 10, 10]}
      b = {"min": [20, 0, 0], "max": [30, 10, 10]}
      result = check_interference(a, b)
      assert result.interferes is False
      assert result.separation_mm == 10
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_assembly_checks.py -q
  ```

### Task 05.3 — Implement adjacency check

**Files:**
- Modify: `src/cad_agent/assembly_checks.py`
- Modify: `tests/test_assembly_checks.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_touching_faces_are_adjacent():
      a = {"min": [0, 0, 0], "max": [10, 10, 10]}
      b = {"min": [10, 0, 0], "max": [20, 10, 10]}
      result = check_adjacency(a, b, tolerance_mm=0.01)
      assert result.adjacent is True
  ```

- [ ] **Step 2: Implement adjacency**
  - Adjacent when boxes touch on one axis and overlap/touch on the other axes.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_assembly_checks.py -q
  ```

### Task 05.4 — Connect assembly validation to workflow gate

**Files:**
- Modify: `src/cad_agent/assembly_checks.py`
- Modify: `src/cad_agent/orchestrator.py`
- Modify: `tests/test_orchestrator.py`, `tests/test_assembly_checks.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_assembly_failure_blocks_export():
      workflow = Workflow()
      workflow.mark_validation_failed(["AABB_INTERFERENCE"])
      result = workflow.request_export()
      assert result.blocked is True
      assert result.reason == "VALIDATION_NOT_PASSED"
  ```

- [ ] **Step 2: Implement gate connection**
  - Assembly validation failure must keep workflow in `validation_failed` or `revision_requested`.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_assembly_checks.py tests/test_orchestrator.py -q
  ```

### Task 05.5 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Verify no full B-Rep or motion validation was added**
  ```bash
  git diff -- src/cad_agent/assembly_checks.py src/cad_agent/orchestrator.py
  ```

- [ ] **Step 2: Run required validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh validate-docs
  bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_assembly_phase1
  git diff --check
  ```

- [ ] **Step 3: Record final verdict**
  - Update `TASKS.md` with status, validation commands, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P05` complete:

- Approved assembly contract document exists.
- Deterministic AABB interference, separation, and adjacency checks have tests.
- Assembly validation report includes reason codes and failure locations.
- Assembly export is blocked unless validation passes and approval gate is satisfied.
- No full B-Rep interference, production assembly storage, PLM/ERP/MES adapters, motion validation, or FEA was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_assembly_phase1
git diff --check
```

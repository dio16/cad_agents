# CAD-P06 — Mechanism DSL and deterministic compiler Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This phase implements deterministic mechanism DSL and compiler behavior only. It does not add real LLM generation.

**Goal:** Implement deterministic mechanism DSL operations and a bounded Specification/Mechanism Plan to Parametric DSL compiler service.

**Architecture:** Add `src/cad_agent/dsl_compiler.py` as an allowlisted compiler. It consumes approved mechanism-plan JSON and emits schema-valid Parametric DSL with traceability metadata.

**Tech Stack:** Python, JSON schemas, pytest, existing Phase 1 DSL validation.

## Global Constraints

- Do not add real LLM generation in this phase unless `CAD-P07` is explicitly merged/split by approval.
- Do not add raw code execution.
- Do not implement motion validation or FEA.
- Do not create production material DB or parts library.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.

## Tasks

### Task 06.1 — Define mechanism DSL allowlist

**Files:**
- Modify: `docs/MECHANISM_DSL_V1.md` or create `docs/MECHANISM_DSL_OPERATIONS.md`
- Create: `tests/test_dsl_compiler.py`

**Interfaces:**
- Consumes: mechanism plan JSON.
- Produces: Parametric DSL JSON.

- [ ] **Step 1: Write failing test for unsupported operation**
  ```python
  def test_compiler_rejects_unsupported_operation():
      plan = {"operations": [{"op": "gear_raw_code", "code": "print('bad')"}]}
      result = compile_mechanism_plan(plan)
      assert result.valid is False
      assert result.reason_code == "UNSUPPORTED_MECHANISM_OP"
  ```

- [ ] **Step 2: Implement allowlist**
  - Accept only approved deterministic operations such as `shaft`, `bearing_seat`, `ring`, `cage`, or the first approved operation set from the contract.
  - Reject anything else.

- [ ] **Step 3: Run test**
  ```bash
  uv run pytest tests/test_dsl_compiler.py::test_compiler_rejects_unsupported_operation -q
  ```

### Task 06.2 — Compile approved mechanism plan to Parametric DSL

**Files:**
- Create: `src/cad_agent/dsl_compiler.py`
- Modify: `tests/test_dsl_compiler.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_compiler_emits_parametric_dsl():
      plan = {"traceability_id": "tr-mech-1", "operations": [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}]}
      result = compile_mechanism_plan(plan)
      assert result.valid is True
      assert result.dsl["units"] == "mm"
      assert result.dsl["traceability_id"] == "tr-mech-1"
  ```

- [ ] **Step 2: Implement compiler**
  - Map approved mechanism operations to Phase 1 Parametric DSL features.
  - Add traceability ID.

- [ ] **Step 3: Add unresolved parameter test**
  ```python
  def test_compiler_rejects_unresolved_parameter_reference():
      plan = {"operations": [{"op": "shaft", "diameter_mm": "$missing"}]}
      result = compile_mechanism_plan(plan)
      assert result.valid is False
      assert result.reason_code == "INVALID_PARAMETER_REFERENCE"
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_dsl_compiler.py -q
  ```

### Task 06.3 — Validate compiler output with Phase 1 schema/AST

**Files:**
- Modify: `src/cad_agent/dsl_compiler.py`
- Modify: `tests/test_dsl_compiler.py`

- [ ] **Step 1: Write failing integration test**
  ```python
  def test_compiler_output_passes_phase1_validation():
      plan = {"traceability_id": "tr-mech-2", "operations": [{"op": "shaft", "diameter_mm": 10, "length_mm": 50}]}
      dsl = compile_mechanism_plan(plan).dsl
      assert validate_phase1_dsl(dsl).passed is True
  ```

- [ ] **Step 2: Implement schema-compatible output**
  - Emit `units=mm`, numeric parameters, executable feature order, and required derivative outputs.

- [ ] **Step 3: Run validation**
  ```bash
  bash ./run_cad_agent.sh phase1-contract-test
  uv run pytest tests/test_dsl_compiler.py -q
  ```

### Task 06.4 — Add approval gate for new operations

**Files:**
- Modify: `src/cad_agent/dsl_compiler.py`, `src/cad_agent/orchestrator.py`
- Modify: `tests/test_dsl_compiler.py`, `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_new_operation_requires_approval():
      result = request_new_operation("custom_gear")
      assert result.requires_human_approval is True
  ```

- [ ] **Step 2: Implement approval marker**
  - New operation requests produce `NEW_OPERATION_APPROVAL_REQUIRED`.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_dsl_compiler.py tests/test_orchestrator.py -q
  ```

### Task 06.5 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Verify no real LLM or raw code execution was added**
  ```bash
  git diff -- src/cad_agent/dsl_compiler.py src/cad_agent/agents
  ```

- [ ] **Step 2: Run required validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh phase1-contract-test
  bash ./run_cad_agent.sh validate-docs
  git diff --check
  ```

- [ ] **Step 3: Record final verdict**
  - Update `TASKS.md` with status, validation commands, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P06` complete:

- Mechanism DSL allowlist is defined.
- Compiler rejects unsupported operations and unresolved parameters.
- Compiler emits Parametric DSL with traceability IDs.
- AST/schema validation passes for golden mechanism fixtures.
- New operation requests require human/reviewer approval.
- Tests cover valid operations, unsupported operations, unresolved parameters, and traceability metadata.
- No real LLM route, production parts library, production material DB, motion validation, FEA, or raw code execution was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest -q
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh validate-docs
git diff --check
```

# CAD-P09 — First target object end-to-end integration Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This is the final integration phase and requires human approval for target spec, validation plan, and export decision.

**Goal:** Integrate approved prior phases into a deterministic end-to-end pipeline for the first target object, likely `gyro_kinetic_v1`.

**Architecture:** Use the `CAD-P03` workflow gate as the integration spine. Feed approved requirement/spec/DSL/CAD/validation artifacts through the deterministic pipeline and produce a review/export package only after gates pass.

**Tech Stack:** Python, pytest, existing Phase 1/2 pipeline, local artifact store, JSONL audit, `run_cad_agent.sh`.

## Global Constraints

- Do not skip approval/export gates.
- Do not print/export without approval.
- Do not claim production readiness.
- Do not add FEA unless separately approved.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.

## Tasks

### Task 09.1 — Approve target object spec

**Files:**
- Create: `artifacts/gyro_kinetic_v1/target_spec.json` only if explicitly approved
- Modify: `TASKS.md`

**Interfaces:**
- Consumes: approved target object requirements.
- Produces: target specification JSON with approval record.

- [ ] **Step 1: Write failing test for missing approval**
  ```python
  def test_target_spec_requires_approval():
      spec = load_target_spec()
      assert spec["approval"]["specification_freeze"] is True
  ```

- [ ] **Step 2: Implement approval record**
  - Add approval metadata and traceability ID.

- [ ] **Step 3: Run validation**
  ```bash
  uv run pytest tests/test_platform_poc.py -q
  ```

### Task 09.2 — Generate requirement and specification artifacts

**Files:**
- Create: `artifacts/gyro_kinetic_v1/requirement.json`
- Create: `artifacts/gyro_kinetic_v1/specification.json`
- Modify: `tests/test_platform_poc.py` or new `tests/test_target_object.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_target_requirement_schema_valid():
      req = load_json("artifacts/gyro_kinetic_v1/requirement.json")
      assert validate_requirement(req).passed is True
  ```

- [ ] **Step 2: Implement artifact generation**
  - Generate deterministic requirement/spec artifacts from approved inputs.

- [ ] **Step 3: Add spec validation test**
  ```python
  def test_target_spec_schema_valid():
      spec = load_json("artifacts/gyro_kinetic_v1/specification.json")
      assert validate_specification(spec).passed is True
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_target_object.py -q
  ```

### Task 09.3 — Compile target DSL and run CAD

**Files:**
- Create: `artifacts/gyro_kinetic_v1/dsl.json`
- Modify: `src/cad_agent/platform_poc.py` only if needed
- Modify: `tests/test_target_object.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_target_dsl_passes_phase1_validation():
      dsl = load_json("artifacts/gyro_kinetic_v1/dsl.json")
      assert validate_phase1_dsl(dsl).passed is True
  ```

- [ ] **Step 2: Implement compiler output**
  - Emit Phase 1-compatible DSL.

- [ ] **Step 3: Add CAD run test**
  ```python
  def test_target_cad_run_generates_artifact_metadata():
      result = run_target_pipeline()
      assert result.artifacts["metadata"].exists()
  ```

- [ ] **Step 4: Run Phase 1 pipeline**
  ```bash
  bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_target_phase1
  ```

### Task 09.4 — Run validation and approval gate

**Files:**
- Modify: `src/cad_agent/orchestrator.py`
- Modify: `tests/test_target_object.py`, `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_target_export_requires_approval():
      workflow = Workflow()
      workflow.mark_validation_passed()
      result = workflow.request_export()
      assert result.blocked is True
      assert result.reason == "EXPORT_APPROVAL_REQUIRED"
  ```

- [ ] **Step 2: Implement approval gate**
  - Export only after validation pass and approval.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_target_object.py tests/test_orchestrator.py -q
  ```

### Task 09.5 — Produce review package and close phase

**Files:**
- Modify: `TASKS.md`
- Create: `artifacts/gyro_kinetic_v1/review_package.md` only if explicitly approved

- [ ] **Step 1: Write failing test**
  ```python
  def test_review_package_contains_traceability():
      package = load_review_package()
      assert "traceability_id" in package
  ```

- [ ] **Step 2: Implement review package**
  - Include changed files, decisions, validation results, must-fix closure, deferred items, and next phase proposal.

- [ ] **Step 3: Run full validation**
  ```bash
  bash ./run_cad_agent.sh status
  bash ./run_cad_agent.sh validate-docs
  bash ./run_cad_agent.sh phase1-contract-test
  bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_target_phase1
  bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_target_phase2
  bash ./run_cad_agent.sh serve --dry-run
  uv run pytest -q
  git diff --check
  ```

- [ ] **Step 4: Record final verdict**
  - Update `TASKS.md` with status, validation commands, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P09` complete:

- Requirement JSON exists and is schema-valid.
- Specification JSON exists and has approval record.
- Parametric DSL exists and passes schema/AST validation.
- CAD Runtime generates STEP/B-Rep or approved PoC surrogate artifacts with metadata.
- Validation Report records pass/fail and reason codes.
- Approval record exists before print/export.
- Audit log preserves traceability across generated artifacts.
- Full validation suite passes.
- No production release, production artifact store, production API/auth/worker/storage, FEA, PLM/ERP/MES adapters, or unapproved print/export was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
bash ./run_cad_agent.sh status
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_target_phase1
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_target_phase2
bash ./run_cad_agent.sh serve --dry-run
uv run pytest -q
git diff --check
```

# CAD-P03 — Bounded workflow safety gate Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This is the recommended next implementation phase. Keep it local and non-production.

**Goal:** Implement a local in-process workflow safety gate around the existing Phase 1/2 pipeline.

**Architecture:** Add `src/cad_agent/orchestrator.py` as a deterministic state-machine wrapper. It should call existing Phase 1/2 functions but block CAD generation and export unless required approvals exist.

**Tech Stack:** Python, pytest, JSONL audit, existing Phase 1/2 pipeline.

## Global Constraints

- Do not implement a full production Orchestrator service.
- Do not implement production API/auth/worker/storage.
- Do not integrate real LLM endpoints.
- Do not add mechanism DSL, motion validation, FEA, or production CAD features.
- Do not treat this phase as a production workflow engine.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started. Recommended next implementation phase.

## Tasks

### Task 03.1 — Define workflow state machine and audit event shape

**Files:**
- Create: `src/cad_agent/orchestrator.py`
- Create: `tests/test_orchestrator.py`
- Modify as needed: `TASKS.md`

**Interfaces:**
- Consumes: existing Phase 1/2 validation result objects or dictionaries.
- Produces: workflow state, approval decisions, revision requests, and audit events.

- [ ] **Step 1: Write failing test for state transitions**
  ```python
  def test_state_machine_records_spec_approval_transition():
      workflow = Workflow()
      workflow.approve_specification("spec-1")
      assert workflow.state == "spec_approved"
      assert workflow.events[-1]["type"] == "specification_approved"
  ```

- [ ] **Step 2: Implement minimal state machine**
  - States: `created`, `spec_pending_approval`, `spec_approved`, `dsl_generated`, `cad_built`, `validation_running`, `validation_passed`, `validation_failed`, `revision_requested`, `export_pending_approval`, `exported`, `escalated_to_human`.
  - Record JSON-serializable events.

- [ ] **Step 3: Add audit event helper**
  ```python
  def audit_event(event_type: str, **payload: object) -> dict:
      return {"type": event_type, "traceability_id": payload.get("traceability_id"), "payload": payload}
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_orchestrator.py::test_state_machine_records_spec_approval_transition -q
  ```

### Task 03.2 — Enforce spec approval before CAD generation

**Files:**
- Modify: `src/cad_agent/orchestrator.py`
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_cad_generation_blocked_without_spec_approval():
      workflow = Workflow()
      result = workflow.run_cad({"dsl": "golden"})
      assert result.blocked
      assert result.reason == "SPEC_APPROVAL_REQUIRED"
  ```

- [ ] **Step 2: Implement gate**
  - `run_cad()` checks `state == "spec_approved"`.
  - If not approved, return blocked decision without calling CAD runtime.

- [ ] **Step 3: Write passing case**
  ```python
  def test_cad_generation_allowed_after_spec_approval():
      workflow = Workflow()
      workflow.approve_specification("spec-1")
      result = workflow.run_cad({"dsl": "golden"})
      assert not result.blocked
      assert workflow.state == "cad_built"
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_orchestrator.py -q
  ```

### Task 03.3 — Convert validation failure to revision request

**Files:**
- Modify: `src/cad_agent/orchestrator.py`
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_validation_failure_creates_revision_request():
      workflow = Workflow()
      workflow.approve_specification("spec-1")
      result = workflow.handle_validation({"passed": False, "reason_codes": ["WALL_THICKNESS_BELOW_MIN"]})
      assert workflow.state == "revision_requested"
      assert result.revision_request.reason_codes == ["WALL_THICKNESS_BELOW_MIN"]
  ```

- [ ] **Step 2: Implement revision request**
  - Store reason codes and failure locations.
  - Increment failure count.

- [ ] **Step 3: Add escalation test**
  ```python
  def test_three_failures_escalate_to_human():
      workflow = Workflow()
      for _ in range(3):
          workflow.handle_validation({"passed": False, "reason_codes": ["RETRY_FAILURE"]})
      assert workflow.state == "escalated_to_human"
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_orchestrator.py -q
  ```

### Task 03.4 — Enforce export approval gate

**Files:**
- Modify: `src/cad_agent/orchestrator.py`
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test for missing validation**
  ```python
  def test_export_blocked_without_validation_pass():
      workflow = Workflow()
      workflow.approve_specification("spec-1")
      workflow.run_cad({"dsl": "golden"})
      result = workflow.request_export()
      assert result.blocked
      assert result.reason == "VALIDATION_NOT_PASSED"
  ```

- [ ] **Step 2: Implement validation pass requirement**
  - Export requires `state == "validation_passed"`.

- [ ] **Step 3: Write failing test for missing export approval**
  ```python
  def test_export_blocked_without_export_approval():
      workflow = Workflow()
      workflow.mark_validation_passed()
      result = workflow.request_export()
      assert result.blocked
      assert result.reason == "EXPORT_APPROVAL_REQUIRED"
  ```

- [ ] **Step 4: Implement export approval**
  - `approve_export()` moves state to `exported` and records audit event.

- [ ] **Step 5: Run tests**
  ```bash
  uv run pytest tests/test_orchestrator.py -q
  ```

### Task 03.5 — Integrate audit JSONL with Phase 2 style

**Files:**
- Modify: `src/cad_agent/orchestrator.py`
- Modify: `src/cad_agent/phase2_pilot.py` only if needed for shared audit helper
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_audit_jsonl_records_export_decision(tmp_path):
      workflow = Workflow(audit_path=tmp_path / "audit.jsonl")
      workflow.approve_specification("spec-1")
      workflow.mark_validation_passed()
      workflow.approve_export("export-1")
      lines = (tmp_path / "audit.jsonl").read_text().splitlines()
      assert any("export_approved" in line for line in lines)
  ```

- [ ] **Step 2: Implement append-only JSONL writer**
  - Append one JSON object per event.
  - Include `traceability_id`, event type, timestamp, and payload.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_orchestrator.py -q
  ```

### Task 03.6 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`, `docs/cad_agent_implementation_plan.md` only if needed to record evidence

- [ ] **Step 1: Verify forbidden scope was not added**
  ```bash
  git status --short -- api_server.py project_service.py job_queue.py schemas/v1 cad_runtime dsl
  ```
  Expected: no production API/worker/schema changes unless explicitly approved.

- [ ] **Step 2: Run required validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh validate-docs
  bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_orchestrator_phase1
  bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_orchestrator_phase2
  bash ./run_cad_agent.sh serve --dry-run
  git diff --check
  ```

- [ ] **Step 3: Record deviation verdict**
  - If any command fails, keep `TASKS.md` status as `blocked` or `in_progress`.
  - If all pass, mark `CAD-P03` complete with validation IDs and reviewer verdict.

## Completion Deviation Check

Before marking `CAD-P03` complete:

- CAD generation is blocked without `specification_freeze` approval.
- Validation failure creates a revision request with reason codes.
- Three validation failures produce `escalated_to_human`.
- Export/print is blocked unless validation passed and export approval exists.
- Validation override and spec change require approval.
- Audit JSONL records state transitions, approvals, rejections, revision requests, and export decisions.
- No production API/auth/worker/storage, real LLM endpoint, mechanism DSL, motion validation, FEA, or production CAD feature was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-golden-pipeline --output-dir /tmp/cadagent_orchestrator_phase1
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_orchestrator_phase2
bash ./run_cad_agent.sh serve --dry-run
git diff --check
```

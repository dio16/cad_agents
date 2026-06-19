# CAD-P02 — DFM/AM validation pilot Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This phase maintains the local DFM/AM Pilot and does not deploy production workers.

**Goal:** Keep Phase 2 DFM/AM profile validation, worker probes, review diff, audit JSONL, and model gateway probes deterministic and validated.

**Architecture:** The phase uses `src/cad_agent/phase2_pilot.py` as the local pilot entrypoint and writes deterministic reports under `/tmp` during validation.

**Tech Stack:** Python, pytest, local HTML diff artifact, local JSONL audit, model gateway probes.

## Global Constraints

- Do not deploy production workers, queues, auth, or real LLM endpoints.
- Do not approve print/export solely because the pilot passes.
- Do not replace deterministic surrogate behavior with production manufacturing evidence.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Completed Pilot.
- Future work in this phase is maintenance/hardening only unless a reviewer explicitly reopens it.

## Tasks

### Task 02.1 — Maintain DFM/AM profile catalog

**Files:**
- Modify as needed: `src/cad_agent/phase2_pilot.py`
- Test: `tests/test_phase2_pilot.py`

**Interfaces:**
- Consumes: manufacturing profile and validation inputs.
- Produces: DFM/AM pass/fail with reason codes.

- [ ] **Step 1: Write failing test for wall thickness rule**
  ```python
  def test_wall_thickness_below_minimum_fails():
      result = validate_fdm_standard({"wall_thickness_mm": 0.3})
      assert not result.passed
      assert "WALL_THICKNESS_BELOW_MIN" in result.reason_codes
  ```

- [ ] **Step 2: Implement minimal rule**
  - Return `WALL_THICKNESS_BELOW_MIN` when wall thickness is below profile minimum.

- [ ] **Step 3: Add hole diameter regression**
  ```python
  def test_hole_diameter_below_minimum_fails():
      result = validate_fdm_standard({"hole_diameter_mm": 1.0})
      assert not result.passed
      assert "HOLE_DIAMETER_BELOW_MIN" in result.reason_codes
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_phase2_pilot.py -q
  ```

### Task 02.2 — Maintain worker probe determinism

**Files:**
- Modify as needed: `src/cad_agent/phase2_pilot.py`
- Test: `tests/test_phase2_pilot.py`

- [ ] **Step 1: Write failing test for surrogate status**
  ```python
  def test_missing_native_executable_records_surrogate():
      result = probe_worker("freecad", executable_path=None)
      assert result.mode == "deterministic_surrogate"
  ```

- [ ] **Step 2: Implement minimal probe behavior**
  - If executable is absent, record surrogate status instead of failing the whole pilot.

- [ ] **Step 3: Run pilot**
  ```bash
  bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_phase2_review
  ```

### Task 02.3 — Maintain review diff, audit, and model gateway probes

**Files:**
- Modify as needed: `src/cad_agent/phase2_pilot.py`, `src/cad_agent/security_policy.py`
- Test: `tests/test_phase2_pilot.py`, `tests/test_security.py`

- [ ] **Step 1: Write failing test for audit fields**
  ```python
  def test_audit_event_has_required_fields():
      event = create_audit_event("phase2_pilot")
      assert event["data_classification"]
      assert event["retention_days"]
      assert event["model_route"]
  ```

- [ ] **Step 2: Implement audit event shape if missing**
  - Include `data_classification`, `retention_days`, and `model_route`.

- [ ] **Step 3: Add model gateway regression**
  ```python
  def test_confidential_commercial_is_rejected():
      decision = route_model("confidential", "commercial")
      assert decision.allowed is False
      assert decision.route == "onprem_required"
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_phase2_pilot.py tests/test_security.py -q
  ```

### Task 02.4 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`
- Test: `bash ./run_cad_agent.sh phase2-pilot-run`, `git diff --check`

- [ ] **Step 1: Verify no production worker deployment**
  - Confirm no Kubernetes, KServe, vLLM, Argo CD, or production queue configuration was added.

- [ ] **Step 2: Verify plan alignment**
  - Confirm pilot docs state Pilot maturity, not production readiness.

- [ ] **Step 3: Record final evidence**
  - Update `TASKS.md` with validation commands, pass/fail status, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P02` complete:

- `phase2-pilot-run` passes.
- DFM/AM profile checks return pass/fail with reason codes.
- Worker probes record native or surrogate status.
- Review diff HTML artifact is written.
- Audit JSONL includes required fields.
- Model Gateway probes pass.
- No production worker deployment or real LLM endpoint was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_phase2_review
uv run pytest tests/test_phase2_pilot.py tests/test_security.py -q
git diff --check
```

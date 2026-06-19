# CAD-P07 — LLM agents and schema-retry routes Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This phase implements bounded local/mock LLM-agent route functions only. It does not add production LLM endpoints.

**Goal:** Implement bounded local/mock LLM-agent route functions using approved prompts, schema validation, retry policy, and deterministic fallback/golden fixtures when needed.

**Architecture:** Add agent route modules under `src/cad_agent/agents/`. Each route returns structured JSON or structured failure, never raw CAD code.

**Tech Stack:** Python, JSON schema validation, pytest, local/mock route functions.

## Global Constraints

- Do not send confidential, regulated, or export-controlled data to commercial routes without approval.
- Do not allow LLMs to execute raw code or change approved specs alone.
- Do not implement production model infrastructure.
- Do not bypass `CAD-P03` approval/export gate.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.

## Tasks

### Task 07.1 — Create agent route module skeleton

**Files:**
- Create: `src/cad_agent/agents/requirement_extractor.py`
- Create: `src/cad_agent/agents/spec_composer.py`
- Create: `src/cad_agent/agents/mechanism_planner.py`
- Create: `tests/test_agents.py`

**Interfaces:**
- Consumes: human intent text or structured input.
- Produces: schema-valid `Requirement JSON`, `Specification JSON`, or mechanism plan, or structured failure.

- [ ] **Step 1: Write failing test for requirement extractor valid fixture**
  ```python
  def test_requirement_extractor_returns_schema_valid_json():
      result = extract_requirement("Design a small kinetic object.")
      assert result.valid is True
      assert "unknowns" in result.json
      assert "assumptions" in result.json
  ```

- [ ] **Step 2: Implement deterministic local route**
  - Return approved golden fixture or structured failure.
  - Do not call external model endpoints.

- [ ] **Step 3: Run test**
  ```bash
  uv run pytest tests/test_agents.py::test_requirement_extractor_returns_schema_valid_json -q
  ```

### Task 07.2 — Add schema retry policy

**Files:**
- Modify: `src/cad_agent/agents/requirement_extractor.py`
- Modify: `src/cad_agent/agents/spec_composer.py`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_invalid_json_retries_until_valid():
      attempts = ["invalid", '{"valid": true}']
      result = retry_schema(attempts, max_retries=2)
      assert result.valid is True
  ```

- [ ] **Step 2: Implement retry policy**
  - Validate output after each attempt.
  - Stop at max retries.
  - Return structured failure with reason codes.

- [ ] **Step 3: Add max-retry failure test**
  ```python
  def test_max_retry_failure_is_structured():
      result = retry_schema(["invalid", "invalid"], max_retries=2)
      assert result.valid is False
      assert result.reason_code == "SCHEMA_RETRY_EXHAUSTED"
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_agents.py -q
  ```

### Task 07.3 — Enforce model routing policy

**Files:**
- Modify: `src/cad_agent/agents/*`
- Modify: `src/cad_agent/security_policy.py` if needed
- Modify: `tests/test_security.py`, `tests/test_agents.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_confidential_route_requires_onprem_approval():
      decision = route_model("confidential", "commercial")
      assert decision.allowed is False
      assert decision.requires_approval is True
  ```

- [ ] **Step 2: Implement routing guard**
  - Confidential/reg/export-controlled data cannot use commercial routes without approval.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_agents.py tests/test_security.py -q
  ```

### Task 07.4 — Audit agent route decisions

**Files:**
- Modify: `src/cad_agent/agents/*`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_agent_route_audit_records_route(tmp_path):
      result = extract_requirement("Design a small kinetic object.", audit_path=tmp_path / "audit.jsonl")
      event = json.loads((tmp_path / "audit.jsonl").read_text().splitlines()[0])
      assert event["model_route"]
  ```

- [ ] **Step 2: Implement audit event**
  - Include data classification, route, retry count, and schema status.

- [ ] **Step 3: Run tests**
  ```bash
  uv run pytest tests/test_agents.py -q
  ```

### Task 07.5 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Verify no production model endpoint was added**
  ```bash
  git diff -- src/cad_agent/agents
  ```

- [ ] **Step 2: Run required validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh validate-docs
  bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_agents_phase2
  git diff --check
  ```

- [ ] **Step 3: Record final verdict**
  - Update `TASKS.md` with status, validation commands, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P07` complete:

- Requirement Extractor route returns schema-valid `Requirement JSON` or structured failure.
- Spec Composer route returns schema-valid `Specification JSON` or structured failure.
- Mechanism Planner route returns schema-valid mechanism plan or structured failure.
- Schema retry policy is deterministic and auditable.
- Commercial/on-prem routing policy is enforced.
- Tests cover valid JSON, invalid JSON retry, max-retry failure, confidential routing, and audit records.
- No production LLM endpoint, production model gateway, confidential commercial exception without approval, regulated/export-controlled automation, or raw code execution was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_agents_phase2
git diff --check
```

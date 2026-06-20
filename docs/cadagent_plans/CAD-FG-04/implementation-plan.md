# CAD-FG-04 — Agent route hardening decision and implementation Implementation Plan

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Keep local/mock agent fixtures explicitly documented unless the user grants a separate approval for real LLM endpoints.

**Architecture:** If approved only for local hardening, improve deterministic fixtures, schema retry evidence, audit records, and tests without external calls. If approved for real LLM, add endpoint configuration, route enforcement, audit, retry, and security tests.

**Tech Stack:** Python, pytest, local/mock agent route modules, security policy, JSONL audit.

## Global Constraints

- Do not call external LLM endpoints without explicit approval.
- Do not store secrets in repository files.
- Do not add production model infrastructure.
- Do not weaken schema retry or audit behavior.
- Every completion must be recorded in `TASKS.md` only after validation passes.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Not started.
- Classification: `approval_required`.
- Real LLM endpoint integration requires a separate explicit approval.

## Tasks

### Task 04.1 — Document local/mock agent route boundary

**Files:**
- Modify: `docs/cad_agent_implementation_plan.md` or related maintained docs if needed
- Modify: `TASKS.md` only after validation

- [ ] **Step 1: Identify current route maturity**
  - Confirm Requirement/Specification/LLM agents are local fixtures/mock unless explicitly approved otherwise.

- [ ] **Step 2: Update documentation**
  - State that real LLM endpoints remain deferred/forbidden without explicit approval.

### Task 04.2 — Harden local/mock route behavior

**Files:**
- Modify: `src/cad_agent/agents/*`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Add deterministic schema retry evidence**
  - Tests should show invalid JSON/schema outputs produce structured failure reason codes.

- [ ] **Step 2: Add audit regression coverage**
  - Agent route audit records must include route, model routing decision, data classification, retry/schema status, traceability, retention, and timestamps.

### Task 04.3 — Optional real LLM route implementation

**Approval required:** yes, separate from this phase.

**Files:**
- Modify: `src/cad_agent/agents/*`
- Modify: `src/cad_agent/security_policy.py`
- Modify: `tests/test_agents.py`
- Modify: `tests/test_security.py`

- [ ] **Step 1: Add explicit configuration boundary**
  - Endpoint configuration must be environment/config driven and must not be hard-coded into repository files.

- [ ] **Step 2: Enforce model routing**
  - Confidential, regulated, and export-controlled data must not use commercial routes.

- [ ] **Step 3: Add retry and audit tests**
  - Real LLM route must preserve schema retry and audit evidence.

### Task 04.4 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Run targeted tests**
  ```bash
  uv run pytest tests/test_agents.py tests/test_security.py -q
  ```

- [ ] **Step 2: Run full validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_fg04_phase2
  git diff --check
  ```

- [ ] **Step 3: Record final verdict**
  - Update `TASKS.md` with validation commands, reviewer verdict, and deviation-check verdict.

## Completion Deviation Check

Before marking `CAD-FG-04` complete:

- Local/mock agent fixture maturity is documented.
- Real LLM endpoint integration is not started without explicit approval.
- Schema retry evidence and audit records are preserved or improved.
- No secrets or hard-coded endpoints are added.
- Full validation suite passes.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest tests/test_agents.py tests/test_security.py -q
uv run pytest -q
bash ./run_cad_agent.sh phase2-pilot-run --output-dir /tmp/cadagent_fg04_phase2
git diff --check
```

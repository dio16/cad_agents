# CAD-P04 — Local API/project/job/artifact workflow v1 Implementation Plan

> **For agentic workers:** Use this plan task-by-task. This phase hardens the local API skeleton only after `CAD-P03` is implemented or explicitly approved in parallel.

**Goal:** Harden the local API skeleton as an in-process workflow interface for workflow run, revision, and export decisions.

**Architecture:** Wrap the `CAD-P03` orchestrator from `src/cad_agent/orchestrator.py` with bounded local routes in `api_server.py`. Project, job, and artifact state remain in-memory/local.

**Tech Stack:** Python stdlib HTTP server, pytest, local JSON artifacts, `serve --dry-run`.

## Global Constraints

- Do not deploy production API service, auth, worker pool, durable storage, or external queue.
- Do not expose real LLM routes.
- Do not make API skeleton imply production readiness.
- Every phase completion must be recorded in `TASKS.md`.
- Before marking complete, compare the result against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`; record any deviation as blocked.

## Current Status

- Skeleton.

## Tasks

### Task 04.1 — Add local workflow run endpoint

**Files:**
- Modify: `src/cad_agent/api_server.py`
- Modify: `src/cad_agent/orchestrator.py` if needed
- Create: `tests/test_api_server.py` additions

**Interfaces:**
- Consumes: local JSON request with `traceability_id` and approved workflow inputs.
- Produces: workflow state and blocked/allowed decision.

- [ ] **Step 1: Write failing test for unapproved workflow request**
  ```python
  def test_workflow_run_requires_spec_approval(client):
      response = client.post("/v1/workflows/run", json={"traceability_id": "tr-test"})
      assert response.status_code == 400
      assert response.json()["reason"] == "SPEC_APPROVAL_REQUIRED"
  ```

- [ ] **Step 2: Implement local workflow route**
  - Route uses `Workflow` from `orchestrator.py`.
  - Return deterministic JSON decision.

- [ ] **Step 3: Run test**
  ```bash
  uv run pytest tests/test_api_server.py -q
  ```

### Task 04.2 — Add local revision endpoint

**Files:**
- Modify: `src/cad_agent/api_server.py`
- Modify: `tests/test_api_server.py`

- [ ] **Step 1: Write failing test**
  ```python
  def test_revision_endpoint_records_reason_codes(client):
      response = client.post("/v1/revisions", json={"traceability_id": "tr-test", "reason_codes": ["RETRY_FAILURE"]})
      assert response.status_code == 200
      assert response.json()["state"] == "revision_requested"
  ```

- [ ] **Step 2: Implement revision route**
  - Create revision request using orchestrator.
  - Persist local JSON response if needed.

- [ ] **Step 3: Run test**
  ```bash
  uv run pytest tests/test_api_server.py -q
  ```

### Task 04.3 — Add local export decision endpoint

**Files:**
- Modify: `src/cad_agent/api_server.py`
- Modify: `tests/test_api_server.py`

- [ ] **Step 1: Write failing test for blocked export**
  ```python
  def test_export_endpoint_blocks_without_approval(client):
      response = client.post("/v1/exports", json={"traceability_id": "tr-test"})
      assert response.status_code == 400
      assert response.json()["blocked"] is True
  ```

- [ ] **Step 2: Implement export route**
  - Use `CAD-P03` export gate.
  - Return blocked decision when validation or export approval is missing.

- [ ] **Step 3: Add success test**
  ```python
  def test_export_endpoint_allows_approved_export(client):
      client.post("/v1/approvals/export", json={"traceability_id": "tr-test"})
      response = client.post("/v1/exports", json={"traceability_id": "tr-test"})
      assert response.status_code == 200
      assert response.json()["state"] == "exported"
  ```

- [ ] **Step 4: Run tests**
  ```bash
  uv run pytest tests/test_api_server.py -q
  ```

### Task 04.4 — Preserve health and metrics

**Files:**
- Modify: `src/cad_agent/api_server.py`, `src/cad_agent/observability.py`
- Modify: `tests/test_api_server.py`

- [ ] **Step 1: Write regression test**
  ```python
  def test_health_and_metrics_still_work(client):
      assert client.get("/health").status_code == 200
      assert client.get("/metrics").status_code == 200
  ```

- [ ] **Step 2: Run smoke test**
  ```bash
  bash ./run_cad_agent.sh serve --dry-run
  ```

### Task 04.5 — Close phase with deviation check

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Verify no production deployment artifacts were added**
  ```bash
  git status --short -- .github k8s docker-compose.yml Dockerfile schemas/v1
  ```
  Expected: no production deployment files unless explicitly approved.

- [ ] **Step 2: Run required validation**
  ```bash
  uv run pytest -q
  bash ./run_cad_agent.sh serve --dry-run
  bash ./run_cad_agent.sh validate-docs
  git diff --check
  ```

- [ ] **Step 3: Record final verdict**
  - Update `TASKS.md` with status, validation commands, and deviation verdict.

## Completion Deviation Check

Before marking `CAD-P04` complete:

- Local API routes enforce the workflow safety gate.
- `/health` and `/metrics` remain deterministic.
- Project/job/artifact endpoints are in-memory/local only.
- Export endpoint returns blocked decisions when approval or validation is missing.
- Tests cover local API gate behavior.
- `serve --dry-run` passes.
- No production API/auth/worker/storage, external queue, durable artifact store, or real LLM endpoint was added.
- `TASKS.md` records the final verdict.

## Required Validation Commands

```bash
uv run pytest -q
bash ./run_cad_agent.sh serve --dry-run
bash ./run_cad_agent.sh validate-docs
git diff --check
```

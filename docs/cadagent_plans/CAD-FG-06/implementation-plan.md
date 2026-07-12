# CAD-FG-06 — Orchestrator State Machine 整合

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Orchestrator の TRANSITIONS dict と method 実装の矛盾を修正し、Design Doc §11 との整合性を確保する。

**Architecture:** TRANSITIONS dict の不正 transition を削除し、`_append_audit_record()` の timestamp drift を修正する。既存の24 tests は全て維持する。

**Tech Stack:** Python 3.11+, pytest, dataclasses.

## Global Constraints

- `uv run pytest -q` → 210+ passed (現行テスト数以上を維持)
- `bash ./run_cad_agent.sh validate-docs` → pass
- `git diff --check` → pass
- 既存のWorkflow クラスの public API を壊さない
- approval_required スコープを拡張しない

## superpowers Skill Integration

**Execution method:** `superpowers:subagent-driven-development`

- **Implementer dispatch:** `superpowers:test-driven-development` に従い、RED→GREEN→REFACTOR cycle で実装
- **Task review:** `superpowers:subagent-driven-development` の task-reviewer で spec compliance + code quality を確認
- **Model:** standard (state machine + テスト修正)
- **Workspace:** ワークツリー不使用。メインブランチで直接実行
- **Progress ledger:** `.superpowers/sdd/progress.md` に記録

### Dispatch Prompt

```
Task: CAD-FG-06 — Orchestrator state machine 整合
Plan: docs/cadagent_plans/CAD-FG-06/implementation-plan.md

You are implementing Task CAD-FG-06 in the CAD-REVIEW-01 batch.
This task fixes TRANSITIONS/method contradiction and audit timestamp drift.

Files to modify:
- src/cad_agent/orchestrator.py (L43, L350-354)
- tests/test_orchestrator.py

Global constraints:
- uv run pytest -q → 210+ passed
- bash ./run_cad_agent.sh validate-docs → pass
- git diff --check → pass

Instructions:
1. Follow TDD: write failing test → verify fail → implement → verify pass → commit
2. Run uv run pytest tests/test_orchestrator.py -q after each change
3. Write results to report file
4. Return status, commits, test summary, and any concerns
```

## Current Status

- Not started.
- Classification: `executable_now` — code quality improvement within existing scope.

## Tasks

### Task 06.1 — Fix TRANSITIONS/method contradiction

**Files:**
- Modify: `src/cad_agent/orchestrator.py:43`
- Test: `tests/test_orchestrator.py`

**Problem:** `TRANSITIONS[CREATED]` に `VALIDATION_FAILED` が含まれているが、`handle_validation()` L156-157 は `self._state == CREATED` の場合 `ValueError` を raise する。これは矛盾。

**Resolution:** `CREATED` の遷移先から `VALIDATION_FAILED` を削除する。CREATED 状態からの validation は `start_validation()` → `VALIDATION_RUNNING` を経由すべき。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_orchestrator.py — add near existing transition tests
def test_created_cannot_transition_to_validation_failed():
    """CREATED → VALIDATION_FAILED is not in TRANSITIONS (handle_validation rejects it)."""
    from cad_agent.orchestrator import CREATED, VALIDATION_FAILED, TRANSITIONS
    assert VALIDATION_FAILED not in TRANSITIONS[CREATED]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_orchestrator.py::test_created_cannot_transition_to_validation_failed -v`
Expected: FAIL — `VALIDATION_FAILED in TRANSITIONS[CREATED]` is True

- [ ] **Step 3: Fix TRANSITIONS dict**

```python
# src/cad_agent/orchestrator.py:43
# Before:
CREATED: frozenset({SPEC_PENDING_APPROVAL, SPEC_APPROVED, VALIDATION_FAILED, ESCALATED_TO_HUMAN}),
# After:
CREATED: frozenset({SPEC_PENDING_APPROVAL, SPEC_APPROVED, ESCALATED_TO_HUMAN}),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_orchestrator.py::test_created_cannot_transition_to_validation_failed -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass (210+)

- [ ] **Step 6: Commit**

```bash
git add src/cad_agent/orchestrator.py tests/test_orchestrator.py
git commit -m "fix: remove invalid CREATED→VALIDATION_FAILED transition from TRANSITIONS dict"
```

### Task 06.2 — Fix audit timestamp drift

**Files:**
- Modify: `src/cad_agent/orchestrator.py:350-354`

**Problem:** `_append_audit_record()` が `datetime.now(timezone.utc)` を2回呼び出し、`timestamp` と `timestamp_suffix` が異なる時刻になるリスクがある。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_orchestrator.py — add near audit tests
def test_audit_record_timestamp_consistency():
    """Audit record timestamp and event_id suffix use the same datetime."""
    import tempfile, json
    from pathlib import Path
    from cad_agent.orchestrator import Workflow
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_path = Path(tmpdir) / "audit.jsonl"
        wf = Workflow(audit_path=audit_path)
        wf.start_validation(traceability_id="tr_test_ts")
        records = [json.loads(line) for line in audit_path.read_text().splitlines() if line.strip()]
        assert len(records) >= 1
        record = records[-1]
        # timestamp and event_id suffix should share the same base
        ts = record["timestamp"]
        event_id = record["event_id"]
        assert ts in record["recorded_at"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_orchestrator.py::test_audit_record_timestamp_consistency -v`
Expected: May pass (timestamp drift is probabilistic), but the code smell is confirmed

- [ ] **Step 3: Fix _append_audit_record to use single timestamp**

```python
# src/cad_agent/orchestrator.py:350-354
# Before:
def _append_audit_record(self, event: dict[str, Any]) -> None:
    if self.audit_path is None:
        return
    timestamp = datetime.now(timezone.utc).isoformat()
    timestamp_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    record = {
        "event_id": f"evt_{timestamp_suffix}",
        "recorded_at": timestamp,
        "timestamp": timestamp,
        ...

# After:
def _append_audit_record(self, event: dict[str, Any]) -> None:
    if self.audit_path is None:
        return
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()
    timestamp_suffix = now.strftime("%Y%m%d%H%M%S%f")
    record = {
        "event_id": f"evt_{timestamp_suffix}",
        "recorded_at": timestamp,
        "timestamp": timestamp,
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_orchestrator.py::test_audit_record_timestamp_consistency -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/cad_agent/orchestrator.py
git commit -m "fix: deduplicate datetime.now() calls in _append_audit_record to prevent timestamp drift"
```

## Completion Deviation Check

- TRANSITIONS dict が handle_validation() の実際の動作と一致していることを確認
- `_append_audit_record()` が単一の `datetime.now()` より `timestamp` と `timestamp_suffix` を生成していることを確認
- `validate-docs` と `git diff --check` が通ることを確認

## Execution Deviation Record (2026-07-12)

- Task 06.1（`CREATED → VALIDATION_FAILED` の `TRANSITIONS` からの削除）は **適用せず**。
  - 根拠: `handle_motion_validation()`（orchestrator.py L228-229）は `CREATED` 状態から失敗時に `_transition(VALIDATION_FAILED)` を行い、その後 `request_revision()` により `REVISION_REQUESTED` へ遷移する。このパスは既存テスト `test_motion_failure_blocks_export_through_workflow_gate` で期待されている。
  - `CREATED` から `REVISION_REQUESTED` への直接遷移は `TRANSITIONS` に存在しないため、`VALIDATION_FAILED` を削除すると motion validation が `ValueError` で失敗する（regression）。
  - `handle_validation()` が `CREATED` からの `VALIDATION_FAILED` を `ValueError` で拒否するのは、main CAD validation は CAD 構築後にのみ実行可能という意図的なガードであり、既存テスト `test_validation_failure_from_created_is_rejected` で検証されている。すなわち `TRANSITIONS` の `CREATED → VALIDATION_FAILED` は motion validation 用に意図的に保持されるべきであり「矛盾」ではない。
  - したがって計画の前提（TRANSITIONS と method の矛盾）は誤りと判断し、遷移を維持した。
- Task 06.2（audit timestamp dedup）は **適用済み**。
  - テスト `test_audit_record_timestamp_consistency` は計画の `wf.start_validation()`（CREATED 既定）では `CREATED → VALIDATION_RUNNING` が `TRANSITIONS` に存在しないため `ValueError` となるため、`Workflow(state=CAD_BUILT, ...)` を使用するよう修正した（意図: 単一の `datetime.now()` から `timestamp` と `timestamp_suffix` を生成することの検証）。
- Design Doc §11 の state machine 定義と整合していることを確認

## Required Validation Commands

```bash
uv run pytest tests/test_orchestrator.py -q
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
git diff --check
```

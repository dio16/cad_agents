# CAD-FG-12 — Test Quality Improvement

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** テスト品質を改善し、private API の直接使用を排除し、不足カバレッジを追加する。

**Architecture:** private `_transition()` を使用するテストを public API 経由に変更し、combined assembly+motion validation のテストを追加する。

**Tech Stack:** Python 3.11+, pytest.

## Global Constraints

- `uv run pytest -q` → 210+ passed (テスト数が増えること)
- `bash ./run_cad_agent.sh validate-docs` → pass
- `git diff --check` → pass
- 既存テストの動作を変更しない

## superpowers Skill Integration

**Execution method:** `superpowers:subagent-driven-development`

- **Implementer dispatch:** `superpowers:test-driven-development` に従い、RED→GREEN→REFACTOR cycle で実装
- **Task review:** `superpowers:subagent-driven-development` の task-reviewer で spec compliance + code quality を確認
- **Model:** standard (テスト改善、カバレッジ追加)
- **Workspace:** ワークツリー不使用。メインブランチで直接実行
- **Progress ledger:** `.superpowers/sdd/progress.md` に記録
- **Depends on:** CAD-FG-06, CAD-FG-07 完了後に実行

### Dispatch Prompt

```
Task: CAD-FG-12 — Test quality improvement
Plan: docs/cadagent_plans/CAD-FG-12/implementation-plan.md

You are implementing Task CAD-FG-12 in the CAD-REVIEW-01 batch.
This task improves test quality by removing private API usage and adding coverage.

Files to modify:
- tests/test_orchestrator.py
- tests/test_motion_validation.py or tests/test_assembly_checks.py

Global constraints:
- uv run pytest -q → 210+ increased test count
- git diff --check → pass
- Do not change existing test behavior

Instructions:
1. Follow TDD: write failing test → verify fail → implement → verify pass → commit
2. Find tests using _transition() and rewrite to use public API
3. Add combined assembly+motion validation workflow test
4. Run uv run pytest -q after each change
5. Write results to report file
6. Return status, commits, test summary, and any concerns
```

## Current Status

- Not started.
- Classification: `executable_now` — test quality improvement, depends on CAD-FG-06.

## Tasks

### Task 12.1 — Fix tests using private _transition() API

**Files:**
- Modify: `tests/test_orchestrator.py`

**Problem:** テストが private `_transition()` API を直接使用している。public API 経由でテストすべき。

- [ ] **Step 1: Identify tests using _transition()**

```bash
grep -n "_transition" tests/test_orchestrator.py
```

- [ ] **Step 2: Rewrite each test to use public API**

Replace `_transition()` calls with appropriate public method calls:
- `_transition(SPEC_APPROVED)` → `wf.approve_specification(...)`
- `_transition(VALIDATION_RUNNING)` → `wf.start_validation(...)`
- etc.

- [ ] **Step 3: Run test suite**

Run: `uv run pytest tests/test_orchestrator.py -q`
Expected: All tests pass

### Task 12.2 — Add combined assembly+motion validation test

**Files:**
- Test: `tests/test_assembly_checks.py` or `tests/test_motion_validation.py`

**Problem:** assembly validation + motion validation の組み合わせテストがない。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motion_validation.py — add
def test_assembly_then_motion_validation_workflow():
    """Assembly validation followed by motion validation through workflow gates."""
    from cad_agent.orchestrator import Workflow, CREATED, VALIDATION_PASSED
    wf = Workflow(state=CREATED)
    wf.approve_specification("tr_test_combined")
    wf.generate_dsl(traceability_id="tr_test_combined")
    wf.run_cad({"traceability_id": "tr_test_combined", "features": []}, traceability_id="tr_test_combined")
    wf.start_validation(traceability_id="tr_test_combined")

    # Assembly validation passes
    assembly_result = {"passed": True, "reason_codes": [], "failure_locations": [], "analysis_scope": "assembly"}
    decision = wf.handle_assembly_validation(assembly_result, traceability_id="tr_test_combined")
    assert decision.approved is True

    # Motion validation passes
    motion_result = {"valid": True, "reason_code": None, "clearance_mm": 5.0}
    decision = wf.handle_motion_validation(motion_result, traceability_id="tr_test_combined")
    assert decision.approved is True
    assert wf.state == VALIDATION_PASSED
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_motion_validation.py::test_assembly_then_motion_validation_workflow -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass (210+)

### Task 12.3 — Separate golden fixtures from production code

**Files:**
- Modify: `tests/test_platform_poc.py`

**Problem:** Golden fixture が production module に混在している。test fixture は test file 内に留めるべき。

- [ ] **Step 1: Identify golden fixtures in production code**

Check if `golden_requirement`, `golden_specification` etc. in `platform_poc.py` are used only in tests.

- [ ] **Step 2: Move to test fixtures if test-only**

If they are test-only, move to conftest.py or test file. If used in production, document the decision.

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: improve test quality - remove private API usage, add combined validation test"
```

## Completion Deviation Check

- テストが private `_transition()` を使用していないことを確認
- Combined assembly+motion validation テストが追加されていることを確認
- 既存テストの動作が変わっていないことを確認
- テスト数が210以上であることを確認

## Required Validation Commands

```bash
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
git diff --check
```

# CAD-FG-07 — validate_artifacts() 分解

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** `validate_artifacts()` の290行を、責務が明確な小さな関数に分解し、保守性を向上させる。

**Architecture:** 各検証カテゴリ (provenance, dimensions, topology, units, manufacturing) を独立した内部関数に抽出し、`validate_artifacts()` をそれらの orchestrator に変える。public API は変更しない。

**Tech Stack:** Python 3.11+, pytest.

## Global Constraints

- `validate_artifacts()` の public signature を変更しない
- 既存の全テストが通ること
- 分解後の各関数に明確な責務を持つこと
- `git diff --check` → pass

## superpowers Skill Integration

**Execution method:** `superpowers:subagent-driven-development`

- **Implementer dispatch:** `superpowers:test-driven-development` に従い、RED→GREEN→REFACTOR cycle で実装
- **Task review:** `superpowers:subagent-driven-development` の task-reviewer で spec compliance + code quality を確認
- **Model:** standard (複数関数の抽出、テスト維持)
- **Workspace:** ワークツリー不使用。メインブランチで直接実行
- **Progress ledger:** `.superpowers/sdd/progress.md` に記録

### Dispatch Prompt

```
Task: CAD-FG-07 — validate_artifacts() 分解
Plan: docs/cadagent_plans/CAD-FG-07/implementation-plan.md

You are implementing Task CAD-FG-07 in the CAD-REVIEW-01 batch.
This task decomposes the 290-line validate_artifacts() into focused sub-functions.

Files to modify:
- src/cad_agent/platform_poc.py
- tests/test_platform_poc.py

Global constraints:
- validate_artifacts() public signature must not change
- uv run pytest -q → all tests pass
- git diff --check → pass

Instructions:
1. Follow TDD: write failing test for each sub-function → verify fail → implement → verify pass
2. Extract: _validate_provenance, _validate_dimensions, _validate_topology, _validate_units, _validate_manufacturing
3. Rewrite validate_artifacts() as orchestrator calling sub-functions
4. Run uv run pytest tests/test_platform_poc.py -q after each extraction
5. Write results to report file
6. Return status, commits, test summary, and any concerns
```

## Current Status

- Not started.
- Classification: `executable_now` — code quality improvement, no behavior change.

## Tasks

### Task 07.1 — Extract _validate_provenance()

**Files:**
- Modify: `src/cad_agent/platform_poc.py`
- Test: `tests/test_platform_poc.py`

**Problem:** `validate_artifacts()` L447-612 が artifact provenance 検証と dimensions/topology 検証を混合している。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_platform_poc.py — add near existing validate_artifacts tests
def test_validate_artifacts_provenance_only():
    """_validate_provenance() can be called independently for artifact checks."""
    from cad_agent.platform_poc import _validate_provenance
    spec = {"parameter_table": {"length": 50, "width": 30, "height": 20}, "constraints": []}
    dsl = {"traceability_id": "tr_val_test", "features": [{"op": "box"}]}
    runtime_result = {
        "status": "pass",
        "traceability_id": "tr_val_test",
        "bbox_mm": {"length": 50, "width": 30, "height": 20},
        "volume_mm3": 30000.0,
        "artifacts": [],
    }
    result = _validate_provenance(dsl, runtime_result)
    assert isinstance(result, dict)
    assert "failures" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_platform_poc.py::test_validate_artifacts_provenance_only -v`
Expected: FAIL — `_validate_provenance` not defined

- [ ] **Step 3: Extract _validate_provenance() from validate_artifacts()**

Extract lines 448-612 (provenance checks) into:

```python
def _validate_provenance(dsl: dict[str, Any], runtime_result: dict[str, Any]) -> dict[str, Any]:
    """Validate artifact provenance: entries, metadata, hashes, traceability."""
    failures: list[dict[str, Any]] = []
    traceability_id = dsl.get("traceability_id", runtime_result.get("traceability_id", "unknown"))
    artifact_entries = runtime_result.get("artifacts", [])
    provenance_ok = True

    def _append_provenance_failure(reason_code: str, failure_location: str, detail: str) -> None:
        nonlocal provenance_ok
        provenance_ok = False
        _append_failure(failures, reason_code, failure_location, detail)

    # ... (move all provenance checks here)

    return {"failures": failures, "provenance_ok": provenance_ok}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_platform_poc.py::test_validate_artifacts_provenance_only -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

### Task 07.2 — Extract _validate_dimensions()

**Files:**
- Modify: `src/cad_agent/platform_poc.py`

- [ ] **Step 1: Extract bbox/volume checks into _validate_dimensions()**

```python
def _validate_dimensions(runtime_result: dict[str, Any], specification: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate bbox and volume against specification parameter_table."""
    failures: list[dict[str, Any]] = []
    bbox = runtime_result.get("bbox_mm", {}) or {}
    parameter_table = specification.get("parameter_table", {}) or {}
    constraints = specification.get("constraints", [])
    # ... (move dimension checks here)
    return failures
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

### Task 07.3 — Extract _validate_topology()

**Files:**
- Modify: `src/cad_agent/platform_poc.py`

- [ ] **Step 1: Extract topology/output checks into _validate_topology()**

```python
def _validate_topology(runtime_result: dict[str, Any], artifact_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate topology: required outputs, watertight, self_intersection."""
    failures: list[dict[str, Any]] = []
    # ... (move topology checks here)
    return failures
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

### Task 07.4 — Extract _validate_units()

**Files:**
- Modify: `src/cad_agent/platform_poc.py`

- [ ] **Step 1: Extract unit consistency checks into _validate_units()**

```python
def _validate_units(dsl: dict[str, Any], runtime_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate unit consistency between DSL and runtime result."""
    failures: list[dict[str, Any]] = []
    # ... (move unit checks here)
    return failures
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

### Task 07.5 — Extract _validate_manufacturing()

**Files:**
- Modify: `src/cad_agent/platform_poc.py`

- [ ] **Step 1: Extract DFM/AM checks into _validate_manufacturing()**

```python
def _validate_manufacturing(dsl: dict[str, Any], specification: dict[str, Any], runtime_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate manufacturing profile constraints (DFM/AM)."""
    failures: list[dict[str, Any]] = []
    # ... (move manufacturing checks here)
    return failures
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

### Task 07.6 — Refactor validate_artifacts() as orchestrator

**Files:**
- Modify: `src/cad_agent/platform_poc.py:447`

- [ ] **Step 1: Rewrite validate_artifacts() to call sub-functions**

```python
def validate_artifacts(specification: dict[str, Any], dsl: dict[str, Any], runtime_result: dict[str, Any]) -> dict[str, Any]:
    """Validate artifacts against specification. Orchestrates sub-validators."""
    traceability_id = dsl.get("traceability_id", runtime_result.get("traceability_id", "unknown"))
    report_traceability_id = f"tr_val_{traceability_id}"

    provenance = _validate_provenance(dsl, runtime_result)
    dimension_failures = _validate_dimensions(runtime_result, specification)
    topology_failures = _validate_topology(runtime_result, runtime_result.get("artifacts", []))
    unit_failures = _validate_units(dsl, runtime_result)
    manufacturing_failures = _validate_manufacturing(dsl, specification, runtime_result)

    all_failures = provenance["failures"] + dimension_failures + topology_failures + unit_failures + manufacturing_failures
    passed = len(all_failures) == 0
    # ... (build report)
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass (same 210+)

- [ ] **Step 3: Commit**

```bash
git add src/cad_agent/platform_poc.py
git commit -m "refactor: decompose validate_artifacts() into _validate_provenance, _validate_dimensions, _validate_topology, _validate_units, _validate_manufacturing"
```

### Task 07.7 — Add decomposition tests

**Files:**
- Test: `tests/test_platform_poc.py`

- [ ] **Step 1: Add tests for each extracted function**

Test that each sub-function can be called independently and returns expected shape.

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

## Completion Deviation Check

- `validate_artifacts()` の public signature が変わっていないことを確認
- 各 sub-function が明確な責務を持っていることを確認
- 全テストが通ることを確認
- Design Doc の validation pipeline と整合していることを確認

## Required Validation Commands

```bash
uv run pytest tests/test_platform_poc.py -q
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
git diff --check
```

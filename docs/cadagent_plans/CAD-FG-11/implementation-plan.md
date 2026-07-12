# CAD-FG-11 — Error Handling Expansion

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** BOOLEAN_FAILED, KERNEL_TIMEOUT error code を追加し、CAD build path の例外処理を改善する。

**Architecture:** `platform_poc.py` に新しい error code 定数を追加し、`run_cad_runtime()` の exception catch を broad にする。

**Tech Stack:** Python 3.11+, pytest.

## Global Constraints

- `uv run pytest -q` → 210+ passed
- `bash ./run_cad_agent.sh validate-docs` → pass
- `git diff --check` → pass
- 既存の error code 定義との一貫性を維持

## superpowers Skill Integration

**Execution method:** `superpowers:subagent-driven-development`

- **Implementer dispatch:** `superpowers:test-driven-development` に従い、RED→GREEN→REFACTOR cycle で実装
- **Task review:** `superpowers:subagent-driven-development` の task-reviewer で spec compliance + code quality を確認
- **Model:** cheap (定数追加 + exception catch 拡張)
- **Workspace:** ワークツリー不使用。メインブランチで直接実行
- **Progress ledger:** `.superpowers/sdd/progress.md` に記録

### Dispatch Prompt

```
Task: CAD-FG-11 — Error handling expansion
Plan: docs/cadagent_plans/CAD-FG-11/implementation-plan.md

You are implementing Task CAD-FG-11 in the CAD-REVIEW-01 batch.
This task adds BOOLEAN_FAILED/KERNEL_TIMEOUT error codes and broadens CAD build exception handling.

Files to modify:
- src/cad_agent/platform_poc.py
- tests/test_platform_poc.py

Global constraints:
- Existing error code definitions must remain consistent
- uv run pytest -q → 210+ passed
- git diff --check → pass

Instructions:
1. Follow TDD: write failing test → verify fail → implement → verify pass → commit
2. Add BOOLEAN_FAILED = "BOOLEAN_FAILED" and KERNEL_TIMEOUT = "KERNEL_TIMEOUT" constants
3. Broaden exception catch to include RuntimeError
4. Run uv run pytest tests/test_platform_poc.py -q after each change
5. Write results to report file
6. Return status, commits, test summary, and any concerns
```

## Current Status

- Not started.
- Classification: `executable_now` — error handling improvement within existing scope.

## Tasks

### Task 11.1 — Add BOOLEAN_FAILED and KERNEL_TIMEOUT error codes

**Files:**
- Modify: `src/cad_agent/platform_poc.py`
- Test: `tests/test_platform_poc.py`

**Problem:** Design Doc で定義されている `BOOLEAN_FAILED`, `KERNEL_TIMEOUT` error code が実装にない。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_platform_poc.py — add near error code tests
def test_boolean_failed_error_code_defined():
    """BOOLEAN_FAILED error code should be available for future boolean operations."""
    from cad_agent.platform_poc import BOOLEAN_FAILED
    assert BOOLEAN_FAILED == "BOOLEAN_FAILED"

def test_kernel_timeout_error_code_defined():
    """KERNEL_TIMEOUT error code should be available for CAD kernel timeout."""
    from cad_agent.platform_poc import KERNEL_TIMEOUT
    assert KERNEL_TIMEOUT == "KERNEL_TIMEOUT"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_platform_poc.py::test_boolean_failed_error_code_defined -v`
Expected: FAIL — BOOLEAN_FAILED not defined

- [ ] **Step 3: Add error codes**

```python
# src/cad_agent/platform_poc.py — add near other error code definitions
BOOLEAN_FAILED = "BOOLEAN_FAILED"
KERNEL_TIMEOUT = "KERNEL_TIMEOUT"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_platform_poc.py::test_boolean_failed_error_code_defined tests/test_platform_poc.py::test_kernel_timeout_error_code_defined -v`
Expected: PASS

### Task 11.2 — Broaden exception handling in CAD build path

**Files:**
- Modify: `src/cad_agent/platform_poc.py:319`

**Problem:** `run_cad_runtime()` L319 が `(KeyError, TypeError, ValueError)` のみ catch し、CadQuery の `RuntimeError` を逃す。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_platform_poc.py — add near CAD build tests
def test_cad_build_runtime_error_captured():
    """RuntimeError from CadQuery should be captured as CAD_BUILD_FAILED."""
    from unittest.mock import patch
    from cad_agent.platform_poc import run_cad_runtime
    dsl = {
        "traceability_id": "tr_test_runtime_err",
        "units": "mm",
        "parameters": {"x": 10.0},
        "features": [{"op": "box", "length_mm": "$x", "width_mm": 10.0, "height_mm": 10.0}],
        "derivative_outputs": ["step_ap242", "stl"],
    }
    with patch("cad_agent.platform_poc._build_cadquery_model", side_effect=RuntimeError("kernel error")):
        # Force CadQuery path
        with patch("cad_agent.platform_poc._cadquery_available", return_value=True):
            result = run_cad_runtime(dsl)
    assert result["status"] == "fail"
    assert result["reason_code"] == "CAD_BUILD_FAILED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_platform_poc.py::test_cad_build_runtime_error_captured -v`
Expected: FAIL — RuntimeError not caught

- [ ] **Step 3: Broaden exception handling**

```python
# src/cad_agent/platform_poc.py:319
# Before:
except (KeyError, TypeError, ValueError) as exc:

# After:
except (KeyError, TypeError, ValueError, RuntimeError) as exc:
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_platform_poc.py::test_cad_build_runtime_error_captured -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/cad_agent/platform_poc.py tests/test_platform_poc.py
git commit -m "feat: add BOOLEAN_FAILED/KERNEL_TIMEOUT error codes and broaden CAD build exception handling"
```

## Completion Deviation Check

- BOOLEAN_FAILED, KERNEL_TIMEOUT が定義されていることを確認
- RuntimeError が CAD build path で catch されることを確認
- 既存の error code 定義と一貫していることを確認
- 全テストが通ることを確認

## Required Validation Commands

```bash
uv run pytest tests/test_platform_poc.py -q
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
git diff --check
```

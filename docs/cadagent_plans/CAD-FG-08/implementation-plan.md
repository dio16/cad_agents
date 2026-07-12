# CAD-FG-08 — DSL Compiler Cleanup

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** DSL compiler の dead parameter と code smell を修正し、コード品質を向上させる。

**Architecture:** `_resolve_dimension()` の未使用 `parameter_name` パラメータを削除し、呼び出し側を更新する。既存の10 tests は全て維持する。

**Tech Stack:** Python 3.11+, pytest.

## Global Constraints

- `uv run pytest -q` → 210+ passed
- `bash ./run_cad_agent.sh validate-docs` → pass
- `git diff --check` → pass
- DSL compiler の public API (`compile_mechanism_plan`, `CompileResult`) を変更しない

## superpowers Skill Integration

**Execution method:** `superpowers:subagent-driven-development`

- **Implementer dispatch:** `superpowers:test-driven-development` に従い、RED→GREEN→REFACTOR cycle で実装
- **Task review:** `superpowers:subagent-driven-development` の task-reviewer で spec compliance + code quality を確認
- **Model:** cheap (1ファイル、明確な dead parameter 削除)
- **Workspace:** ワークツリー不使用。メインブランチで直接実行
- **Progress ledger:** `.superpowers/sdd/progress.md` に記録

### Dispatch Prompt

```
Task: CAD-FG-08 — DSL compiler cleanup
Plan: docs/cadagent_plans/CAD-FG-08/implementation-plan.md

You are implementing Task CAD-FG-08 in the CAD-REVIEW-01 batch.
This task removes the dead parameter_name from _resolve_dimension().

Files to modify:
- src/cad_agent/dsl_compiler.py (L200-208, callers at L132-136, L193)
- tests/test_dsl_compiler.py

Global constraints:
- compile_mechanism_plan public API must not change
- uv run pytest -q → 210+ passed
- git diff --check → pass

Instructions:
1. Follow TDD: write failing test → verify fail → implement → verify pass → commit
2. Remove parameter_name from _resolve_dimension signature and all callers
3. Run uv run pytest tests/test_dsl_compiler.py -q after change
4. Write results to report file
5. Return status, commits, test summary, and any concerns
```

## Current Status

- Not started.
- Classification: `executable_now` — code cleanup, no behavior change.

## Tasks

### Task 08.1 — Remove dead parameter_name in _resolve_dimension()

**Files:**
- Modify: `src/cad_agent/dsl_compiler.py:200-208`
- Modify: `src/cad_agent/dsl_compiler.py:132-136` (callers)

**Problem:** `_resolve_dimension()` が `parameter_name` を受け取り L208 で即 `del parameter_name` している。未使用パラメータ。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dsl_compiler.py — add near existing tests
def test_resolve_dimension_no_parameter_name():
    """_resolve_dimension should not accept a parameter_name argument."""
    import inspect
    from cad_agent.dsl_compiler import _resolve_dimension
    sig = inspect.signature(_resolve_dimension)
    assert "parameter_name" not in sig.parameters, "_resolve_dimension should not have parameter_name"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dsl_compiler.py::test_resolve_dimension_no_parameter_name -v`
Expected: FAIL — parameter_name still exists

- [ ] **Step 3: Remove parameter_name from _resolve_dimension()**

```python
# src/cad_agent/dsl_compiler.py:200-208
# Before:
def _resolve_dimension(
    operation: dict[str, Any],
    key: str,
    plan_parameters: dict[str, Any],
    generated_parameters: dict[str, float],
    parameter_name: str,
    allow_direct_number: bool = False,
) -> CompileResult:
    del parameter_name
    ...

# After:
def _resolve_dimension(
    operation: dict[str, Any],
    key: str,
    plan_parameters: dict[str, Any],
    generated_parameters: dict[str, float],
    allow_direct_number: bool = False,
) -> CompileResult:
    ...
```

- [ ] **Step 4: Update callers**

```python
# src/cad_agent/dsl_compiler.py:132-136 — _compile_shaft callers
# Before:
diameter = _resolve_dimension(operation, "diameter_mm", plan_parameters, generated_parameters, radius_name, allow_direct_number=True)
length = _resolve_dimension(operation, "length_mm", plan_parameters, generated_parameters, length_name, allow_direct_number=True)

# After:
diameter = _resolve_dimension(operation, "diameter_mm", plan_parameters, generated_parameters, allow_direct_number=True)
length = _resolve_dimension(operation, "length_mm", plan_parameters, generated_parameters, allow_direct_number=True)
```

```python
# src/cad_agent/dsl_compiler.py:193 — _validate_phase1_feature caller
# Before:
check = _resolve_dimension(feature, key, parameters, {}, f"feature_{index}_{key}")

# After:
check = _resolve_dimension(feature, key, parameters, {})
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_dsl_compiler.py::test_resolve_dimension_no_parameter_name -v`
Expected: PASS

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass (210+)

- [ ] **Step 7: Commit**

```bash
git add src/cad_agent/dsl_compiler.py tests/test_dsl_compiler.py
git commit -m "fix: remove dead parameter_name from _resolve_dimension and update callers"
```

## Completion Deviation Check

- `_resolve_dimension()` が `parameter_name` パラメータを持っていないことを確認
- 全 caller が更新されていることを確認
- `compile_mechanism_plan` の public API が変わっていないことを確認
- 全テストが通ることを確認

## Required Validation Commands

```bash
uv run pytest tests/test_dsl_compiler.py -q
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
git diff --check
```

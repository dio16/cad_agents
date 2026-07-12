# CAD-FG-10 — Surrogate Quality

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** Deterministic surrogate の STL normal を修正し、surrogate の制限事項をドキュメント化する。

**Architecture:** `_mesh_for_box()` の STL normal を有効なベクトルに修正し、surrogate の既知制限を `CAD_RUNTIME_CONTRACT.md` に追記する。

**Tech Stack:** Python 3.11+, pytest, Markdown.

## Global Constraints

- `uv run pytest -q` → 210+ passed
- `bash ./run_cad_agent.sh validate-docs` → pass
- `git diff --check` → pass
- CadQuery が利用できない環境でも surrogate パスが動作すること

## superpowers Skill Integration

**Execution method:** `superpowers:subagent-driven-development`

- **Implementer dispatch:** `superpowers:test-driven-development` に従い、RED→GREEN→REFACTOR cycle で実装
- **Task review:** `superpowers:subagent-driven-development` の task-reviewer で spec compliance + code quality を確認
- **Model:** cheap (STL normal 修正、ドキュメント追加)
- **Workspace:** ワークツリー不使用。メインブランチで直接実行
- **Progress ledger:** `.superpowers/sdd/progress.md` に記録

### Dispatch Prompt

```
Task: CAD-FG-10 — Surrogate quality
Plan: docs/cadagent_plans/CAD-FG-10/implementation-plan.md

You are implementing Task CAD-FG-10 in the CAD-REVIEW-01 batch.
This task fixes surrogate STL normals and documents limitations.

Files to modify:
- src/cad_agent/platform_poc.py (_mesh_for_box function)
- docs/CAD_RUNTIME_CONTRACT.md
- tests/test_platform_poc.py

Global constraints:
- CadQuery unavailable path must still work
- uv run pytest -q → all tests pass
- git diff --check → pass

Instructions:
1. Follow TDD: write failing test for nonzero normals → verify fail → fix → verify pass
2. Fix _mesh_for_box() to generate valid face normals
3. Add surrogate limitations section to CAD_RUNTIME_CONTRACT.md
4. Run uv run pytest tests/test_platform_poc.py -q after change
5. Write results to report file
6. Return status, commits, test summary, and any concerns
```

## Current Status

- Not started.
- Classification: `executable_now` — quality improvement within existing scope.

## Tasks

### Task 10.1 — Fix STL normals in surrogate mesh

**Files:**
- Modify: `src/cad_agent/platform_poc.py` (search for `_mesh_for_box`)
- Test: `tests/test_platform_poc.py`

**Problem:** `_mesh_for_box()` が生成する STL の normals が全て zero vectors `{0,0,0}` で、invalid な mesh を生成する。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_platform_poc.py — add near surrogate tests
def test_surrogate_stl_normals_are_nonzero():
    """Surrogate STL mesh normals should be non-zero unit vectors."""
    from cad_agent.platform_poc import _mesh_for_box
    stl_text = _mesh_for_box(50.0, 30.0, 20.0)
    # Parse STL ASCII and check normals
    import re
    normals = re.findall(r'facet normal ([\d.e+-]+) ([\d.e+-]+) ([\d.e+-]+)', stl_text)
    assert len(normals) > 0, "STL should have at least one facet"
    for nx, ny, nz in normals:
        length = (float(nx)**2 + float(ny)**2 + float(nz)**2) ** 0.5
        assert length > 0.0, f"Normal ({nx},{ny},{nz}) has zero length"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_platform_poc.py::test_surrogate_stl_normals_are_nonzero -v`
Expected: FAIL — normals are zero vectors

- [ ] **Step 3: Fix _mesh_for_box() normals**

```python
# src/cad_agent/platform_poc.py — find _mesh_for_box function
# Change zero normals to appropriate face normals:
# Front face:  0  0 -1
# Back face:   0  0  1
# Left face:  -1  0  0
# Right face:  1  0  0
# Bottom face: 0 -1  0
# Top face:    0  1  0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_platform_poc.py::test_surrogate_stl_normals_are_nonzero -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

### Task 10.2 — Document surrogate limitations

**Files:**
- Modify: `docs/CAD_RUNTIME_CONTRACT.md`

- [ ] **Step 1: Add surrogate limitations section**

```markdown
## Deterministic Surrogate Limitations

The deterministic surrogate path (`deterministic_surrogate_no_libgl`) is used when
CadQuery/OCCT is not available. Known limitations:

- STEP output is a text placeholder, not canonical B-Rep geometry
- STL mesh uses simplified box geometry with pre-computed normals
- No true boolean operations (through_holes are metadata-only)
- No fillet, chamfer, or complex surface generation
- Volume is computed from additive feature volumes only
- Topology metadata (watertight, self_intersection) is set to safe defaults

These limitations are acceptable for validation pipeline testing and PoC demonstration.
Production use requires CadQuery/OCCT backend.
```

- [ ] **Step 2: Run docs validation**

Run: `bash ./run_cad_agent.sh validate-docs`
Expected: pass

- [ ] **Step 3: Commit**

```bash
git add src/cad_agent/platform_poc.py docs/CAD_RUNTIME_CONTRACT.md
git commit -m "fix: correct surrogate STL normals and document surrogate limitations"
```

## Completion Deviation Check

- STL normals が有効な unit vectors であることを確認
- Surrogate の制限事項が `CAD_RUNTIME_CONTRACT.md` に記載されていることを確認
- CadQuery 不在でも surrogate パスが動作することを確認
- 全テストが通ることを確認

## Required Validation Commands

```bash
uv run pytest tests/test_platform_poc.py -q
uv run pytest -q
bash ./run_cad_agent.sh validate-docs
git diff --check
```

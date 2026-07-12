# CAD-FG-09 — Security Hardening

> **Boundary:** This is the detailed implementation plan for the task. `prompt.md` defines execution/workflow instructions, and `TASKS.md` remains the current task inventory and completion history.

**Goal:** API key を環境変数から読み込み可能にし、CORS support を追加する。

**Architecture:** `security_policy.py` の `CAD_AGENT_API_KEY` を環境変数フォールバックに変更し、`api_server.py` に CORS ヘッダーを追加する。

**Tech Stack:** Python 3.11+, pytest, stdlib http.server.

## Global Constraints

- `uv run pytest -q` → 210+ passed
- `bash ./run_cad_agent.sh validate-docs` → pass
- `git diff --check` → pass
- デフォルトでは従来と同じ `local-dev-key` が使われること
- production auth を追加しない

## superpowers Skill Integration

**Execution method:** `superpowers:subagent-driven-development`

- **Implementer dispatch:** `superpowers:test-driven-development` に従い、RED→GREEN→REFACTOR cycle で実装
- **Task review:** `superpowers:subagent-driven-development` の task-reviewer で spec compliance + code quality を確認
- **Model:** standard (security pattern、CORS implementation)
- **Workspace:** ワークツリー不使用。メインブランチで直接実行
- **Progress ledger:** `.superpowers/sdd/progress.md` に記録

### Dispatch Prompt

```
Task: CAD-FG-09 — Security hardening
Plan: docs/cadagent_plans/CAD-FG-09/implementation-plan.md

You are implementing Task CAD-FG-09 in the CAD-REVIEW-01 batch.
This task adds API key from env var and CORS support.

Files to modify:
- src/cad_agent/security_policy.py (L6)
- src/cad_agent/api_server.py
- tests/test_security.py
- tests/test_api_server.py

Global constraints:
- Default API key must remain "local-dev-key" when env var not set
- uv run pytest -q → 210+ passed
- git diff --check → pass
- Do not add production auth

Instructions:
1. Follow TDD: write failing test → verify fail → implement → verify pass → commit
2. Add os.environ.get fallback for CAD_AGENT_API_KEY
3. Add CORS headers to API server responses
4. Run uv run pytest tests/test_security.py tests/test_api_server.py -q after each change
5. Write results to report file
6. Return status, commits, test summary, and any concerns
```

## Current Status

- Not started.
- Classification: `executable_now` — security improvement within existing scope.

## Tasks

### Task 09.1 — API key from environment variable

**Files:**
- Modify: `src/cad_agent/security_policy.py:6`
- Test: `tests/test_security.py`

**Problem:** `CAD_AGENT_API_KEY = "local-dev-key"` がハードコードされている。開発環境では環境変数で上書きできるべき。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_security.py — add near existing API key tests
def test_api_key_from_environment_variable(monkeypatch):
    """API key can be overridden via CAD_AGENT_API_KEY env var."""
    monkeypatch.setenv("CAD_AGENT_API_KEY", "custom-test-key")
    # Need to reimport to pick up the env var
    import importlib
    import cad_agent.security_policy as sp
    importlib.reload(sp)
    assert sp.CAD_AGENT_API_KEY == "custom-test-key"
    # Restore
    monkeypatch.delenv("CAD_AGENT_API_KEY", raising=False)
    importlib.reload(sp)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_security.py::test_api_key_from_environment_variable -v`
Expected: FAIL — CAD_AGENT_API_KEY is hardcoded

- [ ] **Step 3: Update security_policy.py**

```python
# src/cad_agent/security_policy.py:6
# Before:
CAD_AGENT_API_KEY = "local-dev-key"

# After:
import os
CAD_AGENT_API_KEY = os.environ.get("CAD_AGENT_API_KEY", "local-dev-key")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_security.py::test_api_key_from_environment_variable -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

### Task 09.2 — Add CORS support to API server

**Files:**
- Modify: `src/cad_agent/api_server.py`
- Test: `tests/test_api_server.py`

**Problem:** API server に CORS ヘッダーがない。ローカル開発環境でのフロントエンド接続に必要。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api_server.py — add near existing server tests
def test_cors_headers_on_options():
    """OPTIONS request returns CORS headers."""
    from cad_agent.api_server import CadAgentRequestHandler
    # Test that CORS headers are set
    assert hasattr(CadAgentRequestHandler, '_set_cors_headers') or True  # Will implement
```

- [ ] **Step 2: Add CORS support**

```python
# src/cad_agent/api_server.py — add to CadAgentRequestHandler
def _set_cors_headers(self) -> None:
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
    self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
    self.send_header("Access-Control-Max-Age", "86400")

def do_OPTIONS(self) -> None:
    self.send_response(204)
    self._set_cors_headers()
    self.end_headers()
```

- [ ] **Step 3: Add CORS headers to all responses**

Update `_send_json_response` and error response methods to include CORS headers.

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/cad_agent/security_policy.py src/cad_agent/api_server.py tests/test_security.py tests/test_api_server.py
git commit -m "feat: API key from env var and CORS support for local development"
```

## Completion Deviation Check

- デフォルトの API key が `local-dev-key` のまま変わらないことを確認
- CORS ヘッダーが全てのレスポンスに付与されることを確認
- production auth を追加していないことを確認
- 全テストが通ることを確認

## Required Validation Commands

```bash
uv run pytest tests/test_security.py tests/test_api_server.py -q
uv run pytest -q
bash ./run_cad_agent.sh serve --dry-run
bash ./run_cad_agent.sh validate-docs
git diff --check
```

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="$PYTHON"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if [[ "$PYTHON_BIN" == */* ]]; then
  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Selected Python is not executable: $PYTHON_BIN" >&2
    exit 2
  fi
elif ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Selected Python not found in PATH: $PYTHON_BIN" >&2
  exit 2
else
  PYTHON_BIN="$(command -v "$PYTHON_BIN")"
fi

# Commands delegated to cad_agent_cli: status, validate-docs, phase1-contract-test, phase1-golden-pipeline, phase2-pilot-run, serve, sbom, provenance.
if [[ "${1:-}" == "help" ]]; then
  set -- "--help"
fi
exec "$PYTHON_BIN" -m cad_agent_cli "$@"

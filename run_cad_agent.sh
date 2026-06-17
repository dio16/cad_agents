#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it first or run from the project environment." >&2
  exit 127
fi

if [[ "${1:-}" == "help" ]]; then
  set -- "--help"
fi

exec uv run cad-agent "$@"

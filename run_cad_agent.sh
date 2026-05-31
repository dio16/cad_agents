#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$ROOT/.venv/bin/python"
ENTRYPOINT_NAME="run_cad_agent.sh"
LOCAL_ONLY_COMMANDS=(
  "status"
  "completion-status"
  "local-backend-status"
  "local-fabrication-audit"
  "local-assembly-export"
  "onshape-api-budget-report"
  "local-completion-status"
  "local-pose-snapshots"
  "validate"
  "check"
  "audit"
  "motion"
  "solid-audit"
  "geometry-audit"
  "mate-audit"
  "mated-assembly"
  "pose"
  "pose-snapshots"
  "standard-hardware"
)

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Project .venv not found. Run: uv venv && uv pip install -e ." >&2
  exit 2
fi

cd "$ROOT"
export CAD_AGENT_ENTRYPOINT="$ENTRYPOINT_NAME"
export CAD_AGENT_RUNNER="$ROOT/$ENTRYPOINT_NAME"
export CAD_AGENT_SHELL="bash"
unset CAD_AGENT_LOCAL_ONLY
for arg in "$@"; do
  for local_only_command in "${LOCAL_ONLY_COMMANDS[@]}"; do
    if [[ "$arg" == "$local_only_command" ]]; then
      export CAD_AGENT_LOCAL_ONLY="1"
      break 2
    fi
  done
done
"$VENV_PYTHON" scripts/assert_wsl_runtime.py --local-only --write >/dev/null
if [[ "${1:-}" == "--script" ]]; then
  shift
  if [[ $# -eq 0 ]]; then
    echo "run_cad_agent.sh --script requires a Python script path." >&2
    exit 2
  fi
  exec "$VENV_PYTHON" "$@"
fi
exec "$VENV_PYTHON" cad_agent_cli.py "$@"

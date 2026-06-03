#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

cd "$ROOT"

case "${1:-}" in
  status)
    cat <<'EOF'
{
  "status": "aligned",
  "source_proposal": "docs/Origen/Design_document_for_a_machine_design_platform.md",
  "maintained_commands": ["status", "validate-docs"]
}
EOF
    ;;
  validate-docs)
    exec "$PYTHON_BIN" scripts/validate_platform_contracts.py
    ;;
  ""|-h|--help|help)
    cat <<'EOF'
Usage: bash ./run_cad_agent.sh <command>

Commands:
  status         Print repository alignment status.
  validate-docs  Validate that maintained docs/scripts follow the Origen proposal.
EOF
    ;;
  *)
    echo "Unknown command: $1" >&2
    echo "Run: bash ./run_cad_agent.sh --help" >&2
    exit 2
    ;;
esac

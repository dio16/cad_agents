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
  "maintained_commands": ["status", "validate-docs", "phase1-contract-test", "phase1-golden-pipeline", "phase2-pilot-run"]
}
EOF
    ;;
  validate-docs)
    exec "$PYTHON_BIN" scripts/validate_platform_contracts.py
    ;;
  phase1-contract-test)
    exec "$PYTHON_BIN" -m cad_agent.platform_poc contract-test
    ;;
  phase1-golden-pipeline)
    exec "$PYTHON_BIN" -m cad_agent.platform_poc golden-pipeline --output-dir "${2:-artifacts/phase1_poc}"
    ;;
  phase2-pilot-run)
    exec "$PYTHON_BIN" -m cad_agent.phase2_pilot pilot-run --output-dir "${2:-artifacts/phase2_pilot}"
    ;;
  ""|-h|--help|help)
    cat <<'EOF'
Usage: bash ./run_cad_agent.sh <command>

Commands:
  status         Print repository alignment status.
  validate-docs            Validate that maintained docs/scripts follow the Origen proposal.
  phase1-contract-test    Run Phase 1 schema and AST contract tests.
  phase1-golden-pipeline  Run the single-part Phase 1 PoC pipeline.
  phase2-pilot-run        Run Phase 2 pilot adapters, DFM catalog, review diff, audit, and gateway checks.
EOF
    ;;
  *)
    echo "Unknown command: $1" >&2
    echo "Run: bash ./run_cad_agent.sh --help" >&2
    exit 2
    ;;
esac

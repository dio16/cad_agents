# CAD Agents

<!-- Badges (add as needed) -->
<!-- shields.io badges go here once CI is enabled -->

Lightweight, auditable agentic CAD framework that runs deterministic geometry, motion, visibility, and fabrication gates locally. Final artifact verification reads generated files from disk in a fresh WSL process.

- **License:** Apache-2.0
- **Python:** 3.12+
- **Package manager:** UV
- **Backends:** CadQuery + build123d

## Goal

Build a 3D-printable desktop tourbillon spatial-kinetic sculpture object with:
- bold sculptural presence (macro),
- watch-like fine-motion precision (micro),
- real 3D spatial drive across height or axis direction,
- stationary-autonomous-winding input.

Completion requires independent local evidence: local fabrication pass, viewer, STL, BOM, role manifest, motion/contact/visibility/DFAM checks, and a same-generation deliverable package.

For the canonical mission statement, see [`GOAL.md`](./GOAL.md). For scope and backend selection, see [`SPEC.md`](./SPEC.md).

## Why local-first

- Browser automation is used only for visual review.
- Cloud CAD views are review surfaces, not the source of truth.
- Local manifests, local generators, WSL-first validation, and independent reports are the routine path.
- Onshape is optional final-review/share infrastructure only when local gates are insufficient.

This repo no longer depends on Onshape APIs for active delivery.

## Requirements

- WSL 2 (Linux) with Bash
- Python 3.12+
- UV
- CadQuery-capable CAD runtime
- Git

## Setup

Install dependencies with UV, then use the sanctioned Bash runner.

```bash
git clone https://github.com/dio16/cad_agents.git
cd cad_agents

uv venv --python 3.12
uv pip install -e .
```

## Verify setup

```bash
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v31_geometry_contract.json status
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v31_geometry_contract.json completion-status
```

## Usage

All active work must execute from Bash inside WSL using `run_cad_agent.sh`. Direct `python`, `pip`, PowerShell, `pwsh`, `cmd.exe`, and `cad_agent_cli.py` are not valid active-work entrypoints.

Common commands:
- `status`
- `completion-status`
- `local-backend-status`
- `local-fabrication-audit`
- `local-assembly-export`
- `local-completion-status`
- `local-pose-snapshots`
- `check`
- `motion`
- `solid-audit`
- `hardware-context-audit`
- `motion-preview`

## Repository layout

- `cad_agent/` local workflow and CLI entrypoint
- `scripts/` generation and validation scripts
- `manifests/` JSON design contracts
- `docs/` canonical workflow documents
- `reports/` gate, audit, and evidence outputs
- `deliverables/` current fabrication packages

## Documentation

- Operating rules: [`AGENTS.md`](./AGENTS.md)
- Goal and priority order: [`GOAL.md`](./GOAL.md)
- Project specification: [`SPEC.md`](./SPEC.md)
- Execution ledger: [`TASKS.md`](./TASKS.md)

## Contributing

This repository is maintained as a goal-closure CAD system. Contributions should preserve:
- source-of-truth alignment,
- local-first verification path,
- UV-only Python execution policy,
- evidence-backed completion wording.

Do not add cloud-CAD dependencies as the first diagnostic path.

## License

MIT — see [`LICENSE`](./LICENSE).

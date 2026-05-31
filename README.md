# CAD Agent Framework

Local-first workflow framework for agentic CAD modeling, validation, and evidence management.

## Repository Goal

The canonical repository goal lives in `GOAL.md`.

This repository exists to build a 3D-printable **stationary-autonomous-winding** spatial kinetic sculpture based on a tourbillon mechanism: bold at the whole-object scale, watch-like in its fast fine details, and valuable precisely because the force path unfolds through 3D space.

1. operational integrity / truth,
2. reusable design system,
3. goal delivery / evidence production,
4. optional optimization / exploration.

`AGENTS.md` is the canonical operating document. `TASKS.md` is the live execution ledger.
Partial completion does not stop the repository: unresolved gaps against `GOAL.md` stay active unless an external blocker is documented.

## Core Idea

Use browser automation only for visual review. Use deterministic APIs for CAD operations:

- Onshape Translation API for CAD imports
- Onshape Assemblies API for assembly creation and part insertion
- Onshape Assembly transform API for kinematic pose checks
- JSON manifests for repeatable model state

## Quick Start

Run active work from Bash inside WSL. The sanctioned entrypoint is the Bash runner:

```bash
cd /home/diobrando/codex_wsl/cad_agent_framework
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v28_mechanism_contract.json status
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v28_mechanism_contract.json validate
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v28_mechanism_contract.json completion-status
```

The commands above are historical mechanism-package examples, not proof of the current active goal path. For active work, first read `TASKS.md` plus the routed canonical workflow and use the manifest named there.

Do not use PowerShell, `pwsh`, `cmd.exe`, direct `python`, or direct `cad_agent_cli.py` as active-work entrypoints. Evidence outside the Bash runner is not valid completion evidence.

## Layout

- `cad_agent/onshape_client.py`: signed Onshape REST client
- `cad_agent/workflow.py`: import, assembly, capture, and pose workflows
- `cad_agent/transforms.py`: 4x4 transform helpers for Onshape assemblies
- `cad_agent_cli.py`: command-line entry point
- `manifests/`: reusable model manifests
- `docs/mechanical_design_workflow_ja.md`: canonical reusable design workflow
- `docs/front_loaded_design_framework_ja.md`: canonical pre-CAD concept-selection workflow
- `docs/fifty_point_feasibility_sweep_ja.md`: canonical 50-point pre-proposal feasibility sweep
- `docs/kinetic_object_value_framework_ja.md`: canonical kinetic-object value standard
- `docs/skill_governance_ja.md`: canonical workflow / skill governance
- `docs/design_rule_register_ja.md`: canonical design-rule register
- `docs/context_efficiency_playbook_ja.md`: canonical minimal-reading / context-efficiency playbook
- `docs/operating_packet_checklist_ja.md`: canonical restart packet for long-running loops
- `docs/skill_spec_audit_checklist_ja.md`: canonical minimum-spec audit for reusable skills
- `docs/codex_operating_alignment_ja.md`: canonical mapping from official Codex guidance to this repo
- `docs/architecture_ja.md`: Japanese architecture notes

## Safety

Do not commit API keys. The framework reads credentials from environment variables only.

## Environment Setup

This project uses UV for Python and pnpm for Node.js. Both must be installed:

1. Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Install pnpm: `npm i -g pnpm` (one-time)
3. Setup Python environment:
   ```bash
   uv venv
   uv pip install -e .
   ```

All commands MUST execute through the Bash runner:
```bash
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v31_geometry_contract.json status
```

Do NOT use direct `python` invocation, `npm`, or `yarn`. See `AGENTS.md` for policy details.

## Current Scope

The framework intentionally treats browser and cloud-CAD views as review surfaces, not as the source of truth. Local manifests, local generators, WSL-first validation, and independent reports are the routine path; Onshape is optional final-review infrastructure when local gates are insufficient.

## Current Handoff Surface

Do not infer “current” state from a hardcoded version label in this README.

- Machine-readable current delivery index: `deliverables/current_delivery.json`
- Human-readable delivery index: `deliverables/README.md`
- Current claim / limitation summary: `reports/current_goal_summary.json`
- Final closure artifacts: `reports/goal_state.json` and `reports/goal_state_freshness.json`

The current delivery index names the latest published handoff package and viewer entrypoint. The current goal summary says whether that handoff is actually completion evidence or only a candidate package. If those artifacts disagree with prose elsewhere, treat the artifacts and `TASKS.md` as authoritative, then repair the drift.

The earlier V26 self-validation is quarantined and should not be used for completion claims.

# dio16/cad_agents — Goal and Specification

> 状態: draft — 確定前にレビューが必要

## 1. Project Identity

- **Repository:** dio16/cad_agents
- **Execution environment:** WSL (Linux), Bash
- **Package manager:** UV (Python), pnpm (Node.js only when required)
- **Standard production backends:** CadQuery and build123d (both supported; manifest-driven)
- **First product output:** stationary-autonomous-winding desktop tourbillon spatial-kinetic-sculpture object, 3D-printable and backed by independent local fabrication-PASS evidence

## 2. Mission Statement

Build a reusable agentic CAD modeling repository that produces **validated, user-consumable 3D-printable mechanical objects**.

The repository is not a single artifact factory. It is a living design system that:
1. keeps its own truth reliable (P1),
2. grows reusable design capability whenever that capability is blocking delivery (P2),
3. delivers goal-closing evidence on every loop (P4),
4. and only polishes or explores when no P1–P4 work is executable.

## 3. Final Goal

**Produce a 3D-printable desktop tourbillon sculpture object** where:
- the whole object reads as bold kinetic sculpture (macro),
- the fast, fine parts read as watch-like precision (micro),
- force travels through real 3D space across height or axis direction (spatial drive),
- input energy is provided by a stationary-autonomous-winding mechanism (the object winds itself while sitting on the desk),
- every completion-critical claim is backed by independent local fabrication-PASS evidence (WSL, UV, CadQuery/build123d, viewer, STL, BOM, deliverable), without requiring native Onshape to close the goal.

The repository reaches final closure only when `reports/goal_state.json` and `reports/goal_state_freshness.json` pass in the same turn-end sequence, all P1–P3 mission work is closed or externally blocked with evidence, and a same-generation deliverable package (printable STL, viewer entrypoint, preview, BOM, assembly manifest, parity report, entrypoint) is validated.

## 4. Mandatory Infrastructure

### 4.1 Runtime

| Layer | Requirement |
|---|---|
| UV | All Python package management and execution MUST use UV. `uv venv`, `uv run`, `uv pip install`. Direct `python`, `pip`, external venv paths are not valid active-work entrypoints. |
| pnpm | Node.js work (if any) MUST use pnpm. `npm` and `yarn` are not permitted. |
| Bash-only | All active-repository work must execute from Bash inside WSL. The sanctioned entrypoint is `bash ./run_cad_agent.sh ...`. PowerShell, `pwsh`, `cmd.exe`, direct `python`, direct `cad_agent_cli.py` are not valid for active-work or completion evidence. |
| WSL-first validation | Pre-migration reports are legacy-only. `reports/wsl_runtime_proof.json` must pass before any local gate is trusted. |

### 4.2 CAD Backends (both supported)

| Backend | Role |
|---|---|
| **CadQuery / OCP** | Production geometry, STEP/STL, fabrication-package, interference-volume, bbox, assembly STEP/GLB, WSL-serve viewer. |
| **build123d / OCP** | New local prototypes, quick topology experiments, viewer snapshots, GLB/STL/DXF/URDF exports, text-to-CAD harness. |

Switching between backends is manifest-driven. The generator selected by the manifest renders into the gate chain; gates are backend-agnostic once the manifest defines the expected outputs.

### 4.3 Evidence Architecture

The only trusted completion summary is `reports/current_gate_summary.json`. The only fresh closure pair is `reports/goal_state.json` + freshly regenerated `reports/goal_state_freshness.json` in the same turn-end sequence.

Completion evidence is generation-identity-bound: every completion-critical report, viewer, deliverable pointer must belong to one generation identity, not a mixed bundle of individually passing artifacts.

## 5. Current V31 Active Path

After the 2026-05-18 three-layer audit, the active design path is **V31**. The pre-CAD feasibility chain through `geometry-ready` has passed. The current active task is the V31 post-CAD proof bundle:

1. role manifest
2. sampled motion artifact
3. declared contact audit
4. visibility evidence
5. DFAM audit
6. autonomous-winding evidence
7. spatial-drive evidence
8. object-value review
9. user-consumable deliverable
10. current goal closeout

V30 has been downgraded to candidate-only. V22–V27 remain quarantined/local-fabrication evidence, not completion evidence.

## 6. Scope Boundaries

### 6.1 In-Repo Proof

- 3D model reproducibility
- manifest / generator / report / viewer alignment
- user-consumable deliverable package
- object-value brief, hero-view evidence, kinetic-object review
- gear ratios, tooth profile, center distances, interference, visibility, BOM, assembly order
- local-first / WSL-first verification paths
- mechanical-truth evidence from generated geometry (not declaration)

### 6.2 Out-of-Repo Proof (explicitly not claimed)

- real printer / slicer / material final clearance
- long-term wear / warpage / durability
- hand-feeling after physical assembly
- native Onshape closure (optional, never required for local fabrication PASS)
- physical print evidence

## 7. AGENTS.md Architecture

AGENTS.md stays thin (launch-manual surface). Detailed canonical guidance is split into docs/:

| Concern | Canonical doc |
|---|---|
| Mission and priority routing | AGENTS.md (thin) + GOAL.md |
| CAD implementation workflow | docs/mechanical_design_workflow.md |
| Design-rule decisions | docs/design_rule_register.md |
| Claim / completion wording | docs/mechanism_claim_taxonomy.md |
| Backend selection rationale | docs/local_first_cad_backend_strategy.md |
| Skill / workflow governance | docs/skill_governance.md |
| Context-efficiency / operating packet | docs/context_efficiency_playbook.md, docs/operating_packet_checklist.md |
| Codex operating alignment | docs/codex_operating_alignment.md |

## 8. Sourcing and Legacy Repository

- **New remote:** dio16/cad_agents (GitHub)
- **Old remote:** dio16/codex-onshape-cad-agent → archived, no longer authoritative for active V31+ delivery
- **Initial commit strategy:** clean initial commit of the current working tree (UV/pyproject.toml/AGENTS.md/GOAL.md/TASKS.md/docs/deliverables/reports/manifests/scripts), preserving directory provenance. Git history from the old repo is not carried over.
- **`/home/diobrando/cad/tourbillon/`**: will be treated as legacy experimentation directory and will not receive further active-work commits after archive.

## 9. Open Decision Required Before Committing This Draft

1. Confirm `SPEC.md` location: project root (this file) vs `docs/project_specification.md`.
2. Confirm Japanese naming convention: all-root docs should ship JA mirrors, or root stays English and JA copies live in `docs/ja/`.
3. Confirm initial commit scope: include `reports/` and `deliverables/` directories (large, but truth-critical), or start with code + manifests only and commit reports as a separate repo-wide evidence commit.
4. Confirm whether `onshape_client.py` and Onshape-dependent `cad_agent/workflow.py` paths are kept as optional auxiliary modules or moved into an `onshape-legacy/` package boundary.

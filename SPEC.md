# dio16/cad_agents — Project Specification

## 1. Project Identity

- **Repository:** dio16/cad_agents
- **Visibility:** Public
- **License:** Apache-2.0
- **Execution environment:** WSL (Linux), Bash
- **Package manager:** UV (Python, required), pnpm (Node.js, auxiliary)
- **CAD backends:** CadQuery + build123d (both supported; manifest-driven)
- **First product output:** stationary-autonomous-winding desktop tourbillon spatial-kinetic-sculpture object, 3D-printable with independent local fabrication-PASS evidence

## 2. Mission Statement

Build a reusable agentic CAD modeling framework that produces **validated, user-consumable 3D-printable mechanical objects**.

The repository is not a single artifact factory. It is a living design system that:
1. keeps its own truth reliable (P1),
2. grows reusable design capability whenever that capability blocks delivery (P2),
3. delivers goal-closing evidence on every loop (P3),
4. and only polishes or explores when no P1–P3 work is executable.

## 3. Final Goal

**Produce a 3D-printable desktop tourbillon sculpture object** where:
- the whole object reads as bold kinetic sculpture (macro),
- the fast, fine parts read as watch-like precision (micro),
- force travels through real 3D space across height or axis direction (spatial drive),
- input energy is provided by a stationary-autonomous-winding mechanism,
- every completion-critical claim is backed by independent local fabrication-PASS evidence (WSL, UV, CadQuery/build123d, viewer, STL, BOM, deliverable).

Final closure requires `reports/goal_state.json` and freshly regenerated `reports/goal_state_freshness.json` to pass in the same turn-end sequence, all P1–P3 mission work closed or externally blocked with evidence, and a same-generation deliverable package validated.

## 4. Mandatory Infrastructure

### 4.1 Runtime

| Layer | Requirement |
|---|---|
| UV | All Python package management and execution MUST use UV. `uv venv`, `uv run`, `uv pip install`. Direct `python`, `pip`, external venv paths are not valid active-work entrypoints. |
| pnpm | Node.js work (if any) MUST use pnpm. `npm` and `yarn` are not permitted. |
| Bash-only | All active-repository work must execute from Bash inside WSL. The sanctioned entrypoint is `bash ./run_cad_agent.sh ...`. |
| WSL-first validation | `reports/wsl_runtime_proof.json` must pass before any local gate is trusted. |

### 4.2 CAD Backends (both supported)

| Backend | Role |
|---|---|
| **CadQuery / OCP** | Production geometry, STEP/STL, fabrication-package, interference-volume, bbox, assembly STEP/GLB, local viewer. |
| **build123d / OCP** | New local prototypes, quick topology experiments, viewer snapshots, GLB/STL/DXF/URDF exports, text-to-CAD harness. |

Switching between backends is manifest-driven. The generator selected by the manifest renders into the gate chain; gates are backend-agnostic once the manifest defines expected outputs.

### 4.3 Evidence Architecture

The only trusted completion summary is `reports/current_gate_summary.json`. The only fresh closure pair is `reports/goal_state.json` + freshly regenerated `reports/goal_state_freshness.json` in the same turn-end sequence.

Completion evidence is generation-identity-bound: every completion-critical report, viewer, deliverable pointer must belong to one generation identity.

## 5. Active Design Path

The active design path is **V31**. The pre-CAD feasibility chain through `geometry-ready` has passed. The current active task is the V31 post-CAD proof bundle:

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
- physical print evidence

## 7. Repository Structure

| Directory | Purpose |
|---|---|
| `cad_agent/` | Local workflow engine and CLI entrypoint |
| `scripts/` | Generation and validation scripts |
| `manifests/` | JSON design contracts |
| `docs/` | Canonical workflow / design-rule / skill documents |
| `reports/` | Gate, audit, and evidence outputs |
| `deliverables/` | Fabrication packages (STL, STEP, viewer, BOM) |
| `mechanisms/` | Motion contracts, layout graphs |

AGENTS.md stays thin (launch-manual surface). Detailed canonical guidance lives in `docs/`:

| Concern | Canonical doc |
|---|---|
| CAD implementation workflow | `docs/mechanical_design_workflow_ja.md` |
| Design-rule decisions | `docs/design_rule_register_ja.md` |
| Claim / completion wording | `docs/mechanism_claim_taxonomy_ja.md` |
| Backend selection rationale | `docs/local_first_cad_backend_strategy_ja.md` |
| Skill / workflow governance | `docs/skill_governance_ja.md` |
| Context-efficiency / operating packet | `docs/context_efficiency_playbook_ja.md`, `docs/operating_packet_checklist_ja.md` |
| Codex operating alignment | `docs/codex_operating_alignment_ja.md` |

## 8. Public Repository Notes

- This is an Apache-2.0 licensed public repository.
- No cloud-CAD API dependencies are required for active delivery.
- Contributions should preserve: source-of-truth alignment, local-first verification path, UV-only Python execution policy, evidence-backed completion wording.

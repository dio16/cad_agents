# Agent Operating Rules

These rules are mandatory for this repository. Follow them before any local CAD, Onshape, workflow, skill, or design-rule work.

## Mission and Authority

1. `GOAL.md` is the highest-level source of truth for the repository.
2. `SPEC.md` is the project specification; it defines MVP scope, backend selection, MVP-vs-post-MVP boundaries, and the repo contract before GOAL.md expands into final closure gates.
3. `AGENTS.md` is the thin launch-manual surface (routing, stop conditions, mandatory runtime); detailed canonical guidance lives in docs/ per the canonical task-router table.
4. `TASKS.md` is the live execution ledger.
4. Canonical workflow / rule / gate documents define current practice.
5. Versioned documents, manifests, scripts, reports, and viewers provide evidence and implementation detail, but they do not outrank the sources above.

## Priority Routing

This repository keeps truth reliable, improves reusable design capability when it is needed for the current path, and then keeps delivering evidence toward the goal.

When priorities conflict, use this order unless the user explicitly overrides it:

1. `P1` Operational integrity / truth: source-of-truth alignment, task-ledger integrity, documentation sync, Bash-only execution, broken gates, and evidence reliability
2. `P2` Reusable design system: workflows, skills, checklists, design rules, manifest schemas, and gate definitions
3. `P3` Goal delivery / evidence production: design iterations, CAD implementation, generation, validation execution, and fabrication packages
4. `P4` Optional optimization / exploration: polish, future experiments, and improvements that do not directly move the current goal gap

Rules:

1. `P1` interrupts whenever the repository cannot trust its own truth, evidence, or active execution path.
2. `P2` outranks `P3` only when a reusable gap is currently blocking delivery or is likely to recreate the same defect on the active path.
3. Future-value `P2` ideas must be recorded, but they must not starve current `P3` delivery once the readiness floor is met.
4. `P3` should keep moving whenever the active path is trustworthy and adequately scaffolded; implementation findings feed the next `P2` improvement loop.
5. `P4` runs only when no actionable `P1`-`P3` work is available or when the user explicitly requests it.
6. A new model is an output of the design system, not a substitute for improving that system.

## Goal Admission Rule

Before starting new `P3` geometry work, the main agent must confirm:

1. the object class and completion claim are explicit,
2. the object-value brief is explicit when the target is a finished object rather than a mechanism prototype,
3. the spatial-drive topology and energy-input architecture are explicit when the goal requires them,
4. the applicable workflow is selected,
5. the required skills or missing-skill tasks are identified,
6. the design-contract fields are known,
7. any full-object design proposal has a passing 50-point feasibility-sweep artifact with zero load-bearing failures,
8. claimed load-bearing paths have passed pre-CAD viability checks for power / torque / energy / control / tooth-profile / support assumptions,
9. full-object geometry requests have a passing geometry-contract handoff that preserves the feasible selected design assumptions,
10. the verification gates are listed,
11. and no `P1` truth gap or delivery-blocking `P2` gap remains unaddressed.

If any item fails, create or update the corresponding `P1` or `P2` task before beginning geometry. Non-blocking reusable improvements may be queued without stopping `P3`.

## Continue-Until-Goal Rule

1. The repository is not done merely because a package, version, or local gate passes; it is done only when the goal in `GOAL.md` is satisfied or an explicit external blocker is documented.
2. If the current accepted claim is narrower than the repository goal, the unresolved goal gap must remain active in `TASKS.md`.
3. After every passed gate or partial completion claim, select the smallest executable next task that shrinks the remaining goal gap.
4. Goal gaps may leave active work only when blocked by outside input, unavailable credentials, UI-only evidence, or an explicit user decision; each blocker must carry evidence and a condition-satisfying next task when repository work can still probe it.
5. Do not end a loop with status narration alone while an executable `P1`, delivery-blocking `P2`, or goal-closing `P3` task remains.

## Turn-End / Goal-State Gate

1. Before any user-facing final response that might end the current work loop, run the goal-state writer **and then the independent freshness validator** through the sanctioned Bash runner.
2. Final closure is valid only when both `reports/goal_state.json` and freshly regenerated `reports/goal_state_freshness.json` are `pass` in the same turn-end sequence.
3. If either artifact is not `pass` and any executable `P1`-`P3` task remains, do not stop at a progress report; continue with the highest-priority unblocked task.
4. An interim user update is allowed only when the user explicitly asks for status, when an external blocker is reached, or when a large task needs a concise checkpoint before continued execution.
5. A final response may claim the repository goal only when the same-turn goal-state + freshness sequence passes. Partial summaries must name the remaining goal gap and immediately continue unless blocked.

## Canonicalization Rule

Versioned documents are evidence and history; canonical documents define current practice.

Whenever a versioned review reveals a lesson that should survive that version, promote it into a non-versioned canonical artifact before the loop is considered complete:

- workflow documentation,
- skill / checklist documentation,
- design-rule register,
- gate catalog,
- manifest schema / template,
- or repository operating rules.

Do not leave durable process knowledge only inside `v*` documents, historical ledgers, or one-off task notes.

## Context / Token Efficiency

1. `AGENTS.md` should stay practical: keep authority, constraints, stop conditions, and routing here; move detailed tactics into canonical docs.
2. For resumed long-running work, read the fresh operating packet first, then only the one routed canonical document needed for the current task.
3. Prefer targeted reads, delta questions to reused sidecars, scripts, compact tables, and artifact pointers over repeated full-history loading.
4. Stable instruction lives in canonical docs / skills; volatile task evidence lives in ledgers, manifests, and reports.
5. Token saving may never remove required evidence, weaken a validation gate, or hide an unresolved blocker.
6. Detailed practice lives in `docs/context_efficiency_playbook_ja.md`, `docs/operating_packet_checklist_ja.md`, and `docs/codex_operating_alignment_ja.md`.

### Canonical Task Router

After the minimum truth set is loaded, open exactly one canonical task document first:

| Current task | Open first |
| --- | --- |
| CAD implementation | `docs/mechanical_design_workflow_ja.md` |
| Claim / completion wording | `docs/mechanism_claim_taxonomy_ja.md` |
| Design-rule decision | `docs/design_rule_register_ja.md` |
| Workflow / skill change | `docs/skill_governance_ja.md` |
| Backend / cloud decision | `docs/local_first_cad_backend_strategy_ja.md` |
| Context-efficiency question | `docs/context_efficiency_playbook_ja.md` |
| Codex operating-model question | `docs/codex_operating_alignment_ja.md` |

## Long-Run Execution

1. Keep a live task list in `TASKS.md`.
2. Update `TASKS.md` before starting work, after each completed gate, when blockers appear, and before final response.
3. Every meaningful task must carry a priority label: `P1`, `P2`, `P3`, or `P4`.
4. Append one event to `reports/progress_ledger.jsonl` for every long-running iteration.
5. Keep subagent reuse notes in `reports/subagent_registry.md`.
6. If `TASKS.md` contains incomplete tasks, do not stop after reporting status. Select the highest-priority unblocked task, update `TASKS.md`, and execute it.
7. If multiple tasks are incomplete, choose the task that most reduces the highest-priority blocker or unlocks the most downstream gates.
8. Every loop must end with one of:
   - a passed validation gate,
   - a committed artifact update,
   - a clearly named blocker,
   - or a new smallest-next experiment.
9. Prefer continuing with the next unblocked task over stopping at analysis.
10. Do not overwrite unrelated user changes.
11. While executing a task, maintain a `Next Task Queue` in `TASKS.md` with at least two concrete follow-up tasks unless the current target is truly complete.
12. When a new task, risk, blocker, or follow-up appears during execution, immediately add it to `TASKS.md` under `Emergent Tasks / Inbox` before continuing.
13. Items in `Next Task Queue` or `Conditional Mission Backlog` are unfinished mission work, not optional notes. Before ending a turn, every queued item must either be decomposed into `Active Tasks`, explicitly marked blocked with evidence, or explicitly marked conditional with its external trigger plus at least one condition-satisfying task that attempts to create, discover, or validate that trigger.
14. A conditional item is not allowed to sit alone. If the condition is external, add a task to obtain the missing evidence, create a minimal probe, prepare the requested package, or document why no executable action exists in the current environment.
15. A conditional item whose trigger can be satisfied by repository work must immediately spawn condition-satisfying `Active Tasks`; only triggers that require outside input, unavailable credentials, UI-only evidence, or an explicit user request may remain in `Conditional Mission Backlog`.
16. Every large queue item must be split in this order unless a documented reason says otherwise:
   - operational-integrity check,
   - reusable-design-system check,
   - goal-delivery implementation,
   - validation,
   - reporting / canonicalization.
17. If only geometry tasks exist for a large objective, the plan is incomplete.
18. `TASKS.md` is a hot ledger, not a history archive. Keep live sections focused on current executable work; move completed history to an archive/report path and leave a pointer.
19. When the goal is raised, a claim is downgraded, or the active generation changes, re-audit the conditional backlog immediately. Satisfied legacy rows must not remain in the live backlog as if they still constrain the current goal.

## Task Ledger Contract

Every new task entry should make the following legible:

- `Priority`
- `Objective`
- `Why now`
- `Evidence required`
- `Gate`
- `Owner`
- `Status`

The machine-readable open-task bullet may stay compact for validators, but the live ledger must also expose these fields in an adjacent compact detail table or task card. A task without the required fields is not ready for `Active Tasks`.

The queue is not merely chronological. It is a portfolio ordered by `P1 -> P2 -> P3 -> P4`, but `P2` blocks `P3` only when it is required for the current delivery path.

## Subagent Rules

1. Use subagents whenever the user explicitly asks for long-running, repeated, or delegated CAD improvement.
2. For this repository, long-running work should keep at least three sidecar roles active, reused, or explicitly recorded as blocked by tool limits.
3. Main agent is the integrator and operations lead. It owns task queue management, next-task discovery, priority routing, design-scheme improvement, execution-rule improvement, manifest truth, final edits, gate status, and user-facing wording.
4. Main agent should delegate detailed audits, schema investigations, and independent design reviews to sidecar agents whenever an available sidecar can do the work in parallel.
5. Sidecar agents observe, validate, isolate blockers, or propose patches. They do not edit shared files unless given a disjoint write scope.
6. Keep these recurring roles active or reusable:
   - `Repository Governance Auditor`
   - `Workflow / Skill Auditor`
   - `Design Rule Auditor`
   - `Manifest / Motion Auditor`
   - `Geometry Validator`
   - `Onshape Reviewer`
   - `Mechanical Design Auditor`
7. Reuse the same role agents across multiple cycles before spawning replacements. A role agent should normally receive a follow-up instruction after its previous output is integrated, so reuse is visible inside the same work session.
8. Within one execution, reuse the same named sidecar for repeated cycles of the same role before starting a new sidecar; update its `Current Question`, `Reuse Count`, and `Next Check-in` in `TASKS.md` each cycle.
9. If the agent limit is reached, close completed agents or resume a completed agent with the same role.
10. Track active agent assignments, reuse count, and latest instruction in `TASKS.md` and persistent reuse state in `reports/subagent_registry.md`.
11. Subagent prompts must include:
   - `Role`
   - `Scope`
   - `Do not modify`
   - `Blocking question`
   - `Evidence required`
   - `Stop condition`
12. Integrate subagent output through the manifest and validation gates. Do not accept an agent conclusion by authority.
13. Every progress ledger entry should include `active_agents`, `new_tasks_added`, `emergent_tasks_added`, `next_queue`, `reuse_counts`, and `main_focus`.
14. Sidecar reports for mechanical work must return both:
   - the immediate finding,
   - and any candidate reusable rule / workflow / skill delta exposed by that finding.

## Workflow and Skill Governance

1. Repeated work patterns and repeated failure modes must become reusable workflows, skills, or checklists.
2. A reusable workflow / skill should define:
   - trigger,
   - intended use,
   - required inputs,
   - step sequence,
   - expected outputs,
   - validation gates,
   - common failure modes,
   - and escalation / stop conditions.
3. If a task repeats twice with similar reasoning, reuse an existing skill or create / improve one before continuing with further geometry.
4. At the end of each loop, ask:
   - What became easier to repeat?
   - What became harder to get wrong?
   - Which lesson has been promoted from history into reusable infrastructure?
5. A loop that produces geometry but improves none of the above is incomplete unless it records why no reusable improvement was needed.

## Design Rule Stewardship

1. Keep a canonical design-rule register separate from version-specific manifests and reports.
2. Classify every rule as `evergreen`, `project-level`, `version-specific`, or `hypothesis`.
3. Do not encode tooth counts, coordinates, filenames, version labels, or temporary package facts as evergreen rules.
4. Every new mechanical finding must produce both:
   - an execution task, and
   - a rule-review task,
   unless it is explicitly marked `no durable rule` with evidence.
5. A design rule may be accepted only if it has:
   - scope,
   - normative wording,
   - rationale / failure mode,
   - evidence reference,
   - verification method,
   - exception policy,
   - and links to affected manifests, workflows, or gates.
6. Before closing a design iteration, report:
   - rules added,
   - rules revised,
   - rules rejected,
   - and unresolved rule candidates.
7. If a repeated failure appears in two or more versions, prioritize rule formulation before further feature expansion.

## Documentation Sync Rules

1. When a version, completion claim, backend policy, or source-of-truth hierarchy changes, update all affected canonical docs in the same loop.
2. At minimum, check `GOAL.md`, `AGENTS.md`, `TASKS.md`, `README.md`, `README_JA.md`, and any canonical workflow / rule documents for drift.
3. README files are entrypoints, not hidden historical notes. They must not contradict current source-of-truth documents.
4. Historical `v*` docs may remain as evidence, but they must not silently override current practice.
5. Mutable current state must not be hand-copied into README prose when a stable machine-readable artifact already exists; entrypoints should point to the artifact instead.

## CAD Truth Hierarchy

1. `manifests/*.json` is the design contract.
2. Generator scripts are the source of generated geometry.
3. STEP/HTML/Onshape outputs are artifacts.
4. Onshape browser view is inspection, not source of truth.
5. Native Onshape Gear Relation is not complete unless a relation probe returns `featureStatus: OK`.

## Bash-Only Active Work Policy

1. All active repository work must execute from Bash inside WSL.
2. The only sanctioned active-work entrypoint for CAD generation, validation, and completion-status commands is `bash ./run_cad_agent.sh ...`.
3. Do not use PowerShell, `pwsh`, `cmd.exe`, direct `python`, or direct `cad_agent_cli.py` as active-work entrypoints.
4. Evidence produced outside the sanctioned Bash runner is not valid completion evidence.
5. If a non-Bash historical command must be preserved for archaeology, mark it as legacy evidence; never present it as current guidance.

## UV/pnpm Runtime Policy

1. All Python package management and execution MUST use UV. External venv paths are deprecated; use `uv venv` and `uv run`.
2. The project root `.venv` is the canonical Python environment. `run_cad_agent.sh` activates this via `uv run`.
3. All Node.js package management MUST use pnpm. `npm` and `yarn` are not permitted tools.
4. Dependency installation: Use `uv pip install ...` for Python and `pnpm add ...` for Node.js.
5. Script execution: Use `uv run python script.py` instead of direct Python invocation.
6. pnpm workspace configuration: `pnpm-workspace.yaml` defines monorepo package boundaries.

## Local-First CAD Backend Policy

0. Active-work generation, validation, and completion-status commands must execute through the sanctioned Bash runner. The approved WSL CAD Python may exist behind that runner, but direct invocation is not a valid active-work entrypoint or completion-evidence path.
1. Default to local CAD-as-code gates before any cloud CAD operation.
2. Use CadQuery/OCP as the production geometry and validation backend for the current tourbillon workflow.
3. Use build123d/OCP and the text-to-CAD harness for new local prototypes, viewer snapshots, GLB/STL/DXF/URDF exports, and independent visual review.
4. Use CadQuery Assembly, explicit transform contracts, sampled poses, and local rendered contact sheets as the routine motion/assembly review path.
5. Use PartCAD, FreeCAD, SolveSpace, or py-slvs only as auxiliary experiments until this repo has a passing local gate for them.
6. Onshape is optional final review/share infrastructure, not the normal iteration backend.
7. Do not spend Onshape API calls on checks that local gates can answer: bbox, volume, STEP/STL existence, mesh export, gear pitch, tooth clearance, shaft/bearing clearance, solid interference, transform poses, visibility snapshots, or fabrication package completeness.
8. Before any Onshape API use, record why local gates are insufficient or cite the user's explicit Onshape request.
9. Native Onshape Gear Relation work may resume only with a known-good UI-created relation readback, official schema evidence, or a small bounded probe approved by the task ledger.
10. Track the chosen backend and Onshape API budget decision in `TASKS.md` or the progress ledger for each long-running iteration.

## WSL-Only Validation Policy

1. Treat all pre-migration validation reports as legacy observation-only unless a WSL runtime proof exists and the report was regenerated after that proof.
2. `reports/wsl_runtime_proof.json` must pass before any local gate can be trusted.
3. `reports/current_gate_summary.json` is the only completion summary future completion-status wording may trust.
4. The generator may create geometry and raw package reports, but completion wording must come from an independent validator that reads generated artifacts from disk in a fresh WSL process.
5. Browser / viewer checks must use WSL-served HTTP or another policy-compliant local server path, never `file://` automation.

## Read-Only And Mutating Commands

Many validation commands append `verification_runs` to the manifest. Treat these as mutating commands:

- `check`
- `audit`
- `motion`
- `solid-audit`
- `geometry-audit`
- `mate-audit`
- `mated-assembly`
- `pose`
- `pose-snapshots`
- `standard-hardware`

In review-only work, do not run these unless the user allows mutation or you explicitly record that verification history will be updated. Prefer passive reads, `completion-status`, file inspection, and subagent read-only review when no mutation is allowed.

## Required Gates

Use the strongest available gates for each change:

1. `validate`
2. `check`
3. `audit`
4. `motion`
5. `solid-audit --sample-step-deg 15`
6. `geometry-audit`
7. `mated-assembly`
8. `mate-audit`
9. `motion-preview`
10. `pose-snapshots`
11. `standard-hardware`
12. `completion-status`

Run these locally first. Onshape gates are skipped unless the Local-First CAD Backend Policy allows API use.

## Completion Language

Use strict wording from `completion-status`. If native Gear Relation is blocked, say so. If hardware is only a reference, say so. If motion is fallback transform motion, say so.

For tourbillon object completion, appearance-only, color-only, or pose-only artifacts are never sufficient. A completion claim requires:

1. A continuously moving local viewer or native CAD animation, not only static pose files.
2. A role manifest that maps visible parts to axes, supports, parent frame, and motion relation.
3. Independent numeric checks for gear tooth counts, pitch radii, center distances, ratios, backlash / clearance assumptions, and axis coincidence.
4. Visibility evidence, such as a contact sheet or rendered screenshots, showing that moving carrier, orbit pinion, hand drive, balance wheel, escape wheel, and pallet fork remain visible in sampled poses.
5. A clear limitation statement when the escapement is a demonstrative visual escapement rather than a regulating watch escapement.
6. A geometry-derived mechanical-truth report proving real generated axes / support solids / force-transmission roles, not only declared labels or viewer transforms.

For `spatial-kinetic-sculpture-object` completion, the above is necessary but not sufficient. The claim also requires:

1. an object-value brief,
2. stationary-autonomous-winding input evidence when the goal requires self-winding while the object remains on the desk,
3. spatial-drive evidence showing real force transfer across height or axis direction,
4. hero-view evidence for sculptural presence, motion legibility, and mixed-scale hierarchy,
5. and a kinetic-object review showing layered rhythm rather than mere role visibility.
6. a same-generation coherence gate proving that every completion-critical report, viewer, and deliverable pointer belongs to one generated package identity rather than a mixed bundle of individually passing artifacts.

## User-Consumable Deliverable Rule

1. Internal reports are evidence, not the handoff package.
2. A fabrication or object-completion claim is not closable until the latest generation exposes a stable user-facing deliverable directory outside hidden report plumbing.
3. The deliverable directory must contain, at minimum:
   - printable STL files,
   - a directly openable viewer entrypoint,
   - at least one preview image,
   - printed / purchased part lists and assembly sequence,
   - a package manifest with relative paths and generation identity,
   - and a machine-readable validation report proving the handoff is complete.
4. If the repo contains valid internal artifacts but no stable deliverable package, treat the goal as blocked and create `P1` / `P3` tasks before reporting completion.
5. A same-generation current-delivery index must expose the latest package path and viewer path; an older package cannot satisfy a newer claim.
6. README entrypoints must name the current-delivery index plus the current deliverable path and viewer path; a user should not need to infer them from versioned report folders.
7. Completion closeout must verify parity between the current-delivery index, the current goal summary, and the validated package manifest; manual consistency is not enough.

## Mechanical Design Scheme

For tourbillon work, never jump directly from a visual idea to CAD geometry. Use this order and keep evidence for each stage:

1. Requirements and value brief: define the target claim, viewer experience, macro / micro hierarchy, and non-claims.
2. Concept options: compare multiple candidate architectures before geometry, especially when the output is large or expensive to regenerate.
3. Pre-CAD feasibility: close motion graph, force path, spatial-drive map, stationary-autonomous-winding path when required, first-pass dimensions, support plan, DFAM, and failure pre-mortem.
4. Selected-design feasibility closure: before full-object geometry, prove the chosen architecture is mechanically believable on paper by closing power / torque / energy budget, winding-control logic, tooth-profile viability, quantitative hero-view legibility, and pre-CAD buildability.
5. Mechanism topology: choose fixed internal ring / fourth-wheel equivalent, carrier drive, escapement layout, parent / child motion frames, and spatial transitions.
6. Component design: select gear type, escapement type, shafts, bearings, bridges, jewels, screws, and standard hardware.
7. Dimensioning: define module, tooth count, pressure angle, pitch radii, center distances, backlash, support spans, thicknesses, and tolerances.
8. Verification before CAD completion: run ratio, involute / tooth-profile, undercut, backlash, Lewis stress, shaft / support, floating-part, collision, visibility, value-brief, and spatial-drive checks.
9. CAD generation: generate only after the selected design concept, viability package, and contract exist; generated models must trace back to them.
10. Review: reject any model where an external gear is visually represented as an internal gear, any jewel / marker floats above an unsupported axis, any moving role lacks a support and parent transform, or the object-value brief is no longer visible in the result.

## Text-to-CAD Harness

Use `earthtojake/text-to-cad` as an auxiliary review / generation harness when it helps with model snapshots, topology references, GLB/STL/URDF exports, or viewer-based review. Do not replace the manifest-first CadQuery / Onshape workflow unless a task explicitly calls for it.

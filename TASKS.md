# CAD Agent Task List

This file is the live task ledger. Keep only hot execution state here. Cold history lives in `reports/task_history_2026-05-18.md` and the append-only evidence ledgers under `reports/`.

## Current Status

- Current claim: V30 has been downgraded to a candidate package after the 2026-05-18 three-layer audit. It no longer supports completion because it lacks fresh selected-design feasibility, geometry-contract handoff, full-system motion/contact/visibility/DFAM evidence, and autonomous-winding control proof.
- Completion wording: blocked; V30 is not completion evidence. V31 is now the active design path, has passed the corrected pre-CAD chain through `geometry-ready`, and has a first non-completion geometry candidate with ratchet wheel / pawl / slip clutch / barrel / vertical lift solids validated as single solids.
- Goal-state: blocked by design after the audit; this is the correct state until a post-audit implementation closes the V31 evidence bundle.
- Operating-model audit: completed on 2026-05-18. The live method now uses stable entrypoints, a hot-only ledger, a current operating packet, and thinner skill routing before resuming V31 delivery.
- Scope limits remain explicit: watch-grade escapement, regulating balance, self-sustaining oscillation, native Onshape, and physical print evidence are not claimed.

## Active Tasks

- [x] [P1] Audit the current operating model against the live goal path and official Codex guidance; identify fail-open seams, execution drag, and token-waste regressions before more V31 delivery work.
- [x] [P2] Promote the audit findings into canonical repository operating rules, workflow guidance, and reusable skill/checklist structure so the improved method survives this thread.
- [x] [P2] Simplify the hot execution surface (`TASKS.md`, routing rules, repeated gate references) without weakening truth, evidence, or stop conditions.
- [x] [P3] Reconfirm the smallest trustworthy next delivery step after the operating-model cleanup and leave the V31 path ready to continue under the improved system.
- [ ] [P3] Produce the full V31 post-CAD proof bundle: role manifest, sampled motion, declared contacts, visibility, DFAM, autonomous-winding evidence, spatial-drive evidence, object-value review, user deliverable, and current goal closeout.

### Active Task Detail

| Priority | Objective | Why now | Evidence required | Gate | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Audit operating model against current goal path and official Codex guidance | Current rules are strong, but README / ledger / hot-path drift can still misroute work before those rules engage | local canonical-doc audit, official Codex alignment notes, sidecar reports | fail-open seams and waste points are evidence-bound | main + governance sidecars | completed |
| P2 | Canonicalize durable improvements | Reusable lessons must survive beyond this turn | updated canonical docs / checklist / skill references | durable deltas land outside one-off reports | main | completed |
| P2 | Slim hot execution surface | `TASKS.md` is carrying too much cold history for a live ledger | hot/cold split, archive pointer, compact read path | live ledger contains only current state and history is preserved elsewhere | main | completed |
| P3 | Reconfirm next trustworthy V31 step | Operating cleanup must hand back to delivery, not become a cul-de-sac | updated next queue plus active-path check | smallest trustworthy next step is explicit | main | completed |
| P3 | Close full V31 post-CAD proof bundle | This is the unresolved goal-closing delivery task | same-generation role/motion/contact/visibility/DFAM/winding/spatial/value/deliverable evidence | full proof bundle passes and goal closeout can be rerun | main + future validation sidecars | pending |

## Active Subagents

| Role | Agent | Current Question | Scope | Status | Reuse Count | Next Check-in |
| --- | --- | --- | --- | --- | --- | --- |
| Manifest / Motion Auditor | Pascal | What is the smallest next motion-side proof artifact needed for V31? | V31 manifests, current geometry candidate, proof analogues | active | 1 | after proof-gap audit |
| Geometry Validator | Halley | Which geometry-derived proof is still missing before truthful V31 promotion? | V31 generated geometry and generator | active | 1 | after geometry-gap audit |
| Mechanical Design Auditor | Boole | Is V31 still on-contract enough to continue proof generation rather than rewind design? | V31 selected-design docs and geometry candidate | active | 1 | after continuation audit |

## Emergent Tasks / Inbox

- [x] [P1] The live hot path is visually drowned by historical completed tasks; confirmed and fixed through hot/cold split plus archive pointer.
- [x] [P2] The repo has context-efficiency principles but not yet a compact operating packet that defines the minimum work package for long-running Codex loops; fixed with canonical checklist plus generated packet.
- [x] [P2] Official Codex guidance emphasizes short practical `AGENTS.md`, reusable skills, eval-driven loops, artifact verification, and parallel specialized agents; gap audit completed and canonicalized.
- [x] [P3] V31 proof-gap audit confirmed that `motion_validation` is the smallest next load-bearing proof artifact before sampled motion / contact / visibility can be trusted.

## Conditional Mission Backlog

This section contains only current external or explicitly deferred work. Satisfied legacy items are archived rather than kept in the live backlog.

| Order | Task | Owner | External Trigger | Current Block / Gate |
| --- | --- | --- | --- | --- |
| 1 | Native Gear Relation recovery | Onshape Reviewer + main | A UI-created known-good Gear Relation exists for readback comparison | blocked with evidence: current API variants return `ERROR`; next trigger is UI-created known-good relation or official API schema |
| 2 | Full native-complete status | main | Gear Relation probe returns `featureStatus: OK` | blocked until native relation proof exists |
| 3 | Onshape API use | main + Onshape Reviewer | A local-first gate cannot answer the question, or the user explicitly requests cloud review | deferred by local-first policy |
| 4 | Physical print evidence | main + future fabrication review | User requests physical proof or physical validation becomes part of the goal | external; repo-local goal currently stops at validated printable deliverables |

## Next Task Queue

| Order | Task | Active Task Link | Gate |
| --- | --- | --- | --- |
| 1 | V31 motion validation artifact | active V31 proof task | `v31_motion_validation.json` passes and defines the sampled motion basis |
| 2 | V31 sampled motion + declared contact + visibility chain | after motion validation | sampled motion, declared contact, and visibility artifacts all pass |
| 3 | V31 DFAM + object-value + user-facing closeout | after motion/contact/visibility | DFAM, object-value, deliverable, parity, and entrypoint validations pass |
| 4 | V31 final goal closeout | after user-facing closeout | same-turn goal-state and freshness both pass |

## Archive / Evidence Pointers

- Cold task history moved on 2026-05-18: `reports/task_history_2026-05-18.md`
- Append-only iteration history: `reports/progress_ledger.jsonl`
- Persistent sidecar history: `reports/subagent_registry.md`
- Historical package and proof artifacts remain under `reports/` and `deliverables/`

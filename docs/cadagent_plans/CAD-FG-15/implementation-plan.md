# CAD-FG-15 — Detailed-design / implementation gap inventory & remaining-plan formulation

## 1. Goal / scope

- Reconcile `docs/cad_agent_detailed_design.md` (detailed design) against the actual
  implementation (`src/cad_agent/*`, `examples/*`, tests) and the plan artifacts
  (`docs/cad_agent_implementation_plan.md`, `TASKS.md`).
- Make the implementation state and gaps explicit.
- Record remaining implementation as a plannable plan in plan documents.
- Evaluate the remaining plan and run an **adversarial review (案の敵対的review)** of it,
  then brush the plan up.

This task is a **documentation / status-reconciliation** task. Per `TASKS.md` (Status
summary, line 40), current implementation work is documentation reconciliation only
unless a new approval gate explicitly authorizes code work. The `executable_now`
portion of this task is therefore limited to doc/plan reconciliation; all substantive
remaining *code* work below is classified `approval_required` or `deferred`.

## 2. Status reconciliation performed in this task

- **Drift found**: `docs/cad_agent_implementation_plan.md` §4.1 (Functional gap task
  index) lists only `CAD-FG-00`–`CAD-FG-05`. The `CAD-REVIEW-01` batch `CAD-FG-06`–
  `CAD-FG-13` (this session) and `CAD-FG-14` (HTML viewer) are recorded in `TASKS.md`
  but **not** in the plan's §4.1 index → status drift.
- **Drift found (my own session)**: `CAD-FG-14` Refinement C (commit `f9d0ea7`, STL-mesh
  rendering + unlimited rotation) and the `gear_train_v2` changed-dimension test case
  (commit `756c85b`) are not reflected in `TASKS.md`'s `CAD-FG-14` line.
- **Fixes applied in this task**:
  - `docs/cad_agent_implementation_plan.md` §4.1 updated to list `CAD-FG-06`–`CAD-FG-14`
    (+ `gear_train_v2` test case note).
  - `TASKS.md` updated: `CAD-FG-14` line annotated with Refinement C; `gear_train_v2`
    test case recorded; `CAD-FG-15` entry added pointing here.
  - `src/cad_agent/viewer.py` limitation text corrected: STEP (AP242) is a real B-Rep
    when cadquery is available (same model as the STL); only the surrogate path emits a
    STEP placeholder. The viewer renders the STL mesh for ease of canvas rendering.

## 3. Detailed-design → implementation gap inventory

Status legend: **implemented** (bounded PoC/Pilot/skeleton, working), **partial**
(design intent only partly met), **deferred** (explicitly out of current approval
boundary), **n/a** (design section is policy/maturity, not code).

| Design § | Design intent | Implemented component | Status | Notes |
|---|---|---|---|---|
| §3 Goals 1–9 | Req→Spec→DSL→CAD→Validation→report pipeline | `platform_poc`, `schema_gate`, `assembly_checks`, `motion_validation` | implemented (bounded) | Single + multi-part; surrogate/native cadquery path |
| §6 Architecture | Component responsibilities | `agents/*` (mock), `dsl_compiler`, `orchestrator`, `phase2_pilot`, `security_policy` | implemented (skeleton/mock) | LLM agents are local/mock, not production endpoints |
| §7 Artifact ownership | Canonical + derived artifacts | Req/Spec/DSL/STEP/STL/Validation Report | implemented; HTML viewer covers review artifact | glTF/PNG/PDF derived not generated; HTML viewer supersedes for review |
| §8 Contract boundaries | Schema/DSL/Validation/Approval gates | `schema_gate`, `dsl_compiler`, `orchestrator` | implemented | Approval gate enforced by `CAD-P03` workflow |
| §9 CAD Runtime | Native vs surrogate, deterministic, error codes | `platform_poc._build_cadquery_model`, surrogate fallback | implemented (partial) | `GEAR_GENERATION_FAILED` / `ASSEMBLY_CONSTRAINT_FAILED` reserved in contract but not raised in code (no `gear` op; assembly uses AABB only) |
| §10 Validation layers | schema/AST/geometry/DFM-AM/assembly/motion | all present (bounded) | implemented (partial) | Geometry validation is a PoC proxy; assembly = AABB; motion = bounded clearance |
| §11 Orchestrator | State machine, transitions, escalation | `orchestrator.Workflow` + `TRANSITIONS` | implemented | Matches design §11 (escalated_to_human terminal sink) |
| §12 Security/compliance | Data routing, audit | `security_policy`, `phase2_pilot` audit JSONL | implemented | Routing policy enforced for mock agents |
| §13 Risks | Mitigations | design-only | n/a | Reflected as design text |
| §14 Acceptance | Design doc / Phase 1 / **future** | design doc ✅; Phase 1 ✅; future = bounded form of all items | partial | Future acceptance met in *bounded* form; production readiness deferred |
| §16 HTML review artifact | 7-stage flow incl. 設計案review / 案の敵対的review via viewer | `viewer.write_assembly_viewer`, `run_assembly_pipeline` | implemented | Viewer renders actual STL mesh; this task enacts §16's adversarial review on the plan |

**Key finding**: the only genuine *implementation* gaps within the current bounded
approval boundary are minor (reserved error codes unused; geometry proxy is a PoC).
The substantive remaining work is **deferred production scope** (see §4.2). The detailed
design explicitly states (§2, §5, §10) that the full design is not implemented and that
production items are deferred — so this is by-design, not a missing delivery.

## 4. Remaining implementation gaps — classification

### 4.1 `executable_now` (within current approval; documentation/status reconciliation)
- **CAD-FG-15 itself**: record FG-06–14 in plan §4.1, record Refinement C + `gear_train_v2`
  in `TASKS.md`, correct viewer STEP wording. (Done in this task.)
- Optional bounded code candidates (not mandated; each is small and needs no new DSL op):
  - Wire `ASSEMBLY_CONSTRAINT_FAILED` in `assembly_checks` for unsupported placements.
  - Add deterministic geometry-validation proxy (aspect ratio / min feature size) to the
    validation report — **but see adversarial review §7: risk of redundancy with DFM/AM**.

### 4.2 `approval_required` (deferred production — explicit approval before any code)
- Real native worker pools (OCCT/FreeCAD/CadQuery) replacing the deterministic surrogate.
- Real (non-mock) LLM endpoints + production Model Gateway routing.
- Production-grade material DB + PLM/ERP/MES adapters + tenant isolation.
- FEA solver integration — **separate approved safety-analysis phase** (per plan §4 cross-cutting deferral).
- Production dynamic motion simulation (beyond bounded clearance).
- Durable production artifact storage (current store is local/stub).
- Production SLO + regulatory/export-control workflow.
- New DSL operations beyond the allowlist — e.g., `gear` (true involute teeth). Gated by
  safety review per `AGENTS.md` §4.2; requires contract update + `GEAR_GENERATION_FAILED` wiring.
- Production API/auth/worker deployment (Kubernetes, Docker, CI/CD, SBOM signing).

### 4.3 `deferred` / future-phase
- Full B-Rep interference (current = AABB), production assembly storage, PLM adapters.
- FEA (separate safety phase, as above).

## 5. Proposed next-phase plan (ordered, gated)

1. **CAD-FG-15** (this task): documentation/status reconciliation — **done**.
2. **CAD-FG-16 (proposed, `executable_now` candidate)**: bounded geometry-validation proxy
   — add deterministic sanity checks to the validation report; no new DSL op; small,
   low-risk. *Demoted to optional by adversarial review (§8).*
3. **CAD-FG-17 (proposed, `approval_required`)**: `gear` DSL operation (true teeth) —
   adds involute generation + contract update + `GEAR_GENERATION_FAILED` wiring; requires
   human/reviewer approval per `AGENTS.md` §4.2.
4. **Production phases** (P03-production, etc.): `approval_required`; out of bounded scope.

Recommendation: the user should approve exactly one bounded phase (CAD-FG-16 or
CAD-FG-17) to resume code work; everything in §4.2 stays deferred until explicit approval.

## 6. Evaluation of this plan

- **Coverage**: every detailed-design section (§3–§16) is mapped to a status; no section
  is left "unknown". The plan also closes the §4.1 drift that hid completed work.
- **Feasibility**: doc reconciliation is trivially executable and already done. Bounded
  code candidates are small. Deferred items are correctly flagged, not silently dropped.
- **Risk**: the main risk is *misclassifying a deferred item as `executable_now`*, which
  would violate `AGENTS.md`/plan deferrals. Mitigated by explicit classification + named
  approval gates in §4.2/§5.
- **Completeness**: the only real bounded-implementation gap is minor; the bulk is
  correctly deferred. The plan does **not** claim production readiness.
- **Traceability**: this plan is recorded under `docs/cadagent_plans/CAD-FG-15/` and
  cross-referenced from `TASKS.md` and `docs/cad_agent_implementation_plan.md` §4.1.

## 7. Adversarial review (案の敵対的review) — devil's advocate

1. **Is the inventory complete, or are there silent gaps?**
   The plan lists STEP as "real B-Rep when cadquery available". But the **viewer renders
   the STL mesh, not the STEP B-Rep**. A human reviewing via the viewer sees the mesh,
   not the canonical STEP. They are geometrically equivalent (same cadquery model), so
   this is acceptable, but it should be stated explicitly rather than implied. Also:
   when cadquery is **absent**, STEP is a text placeholder AND STL is a simplified box
   mesh — i.e., the surrogate path produces *no* real geometry at all. That is the true
   boundary of "canonical geometry", and it must not be over-claimed.

2. **Does `executable_now` over-reach?**
   The geometry-validation proxy (CAD-FG-16) overlaps with existing DFM/AM profile checks
   (`phase2_pilot`). Adding a second geometry check risks **redundant/competing
   validation** and schema churn. It should be *optional*, not recommended, unless it
   fills a specific gap DFM/AM does not cover.

3. **Are deferred items truly deferred, or actually required by §14 acceptance?**
   Detailed-design §14 "future acceptance" wants "CAD Runtime generates STEP / B-Rep
   artifacts". With cadquery present this **is** met (real AP242). The gap is only in the
   *surrogate* path. So the plan's framing ("STEP canonical generated") is correct *for
   the native path* and must be scoped accordingly. The plan should not imply STEP is
   universally real.

4. **Root cause of the §4.1 drift (process gap).**
   Why were FG-06–14 never added to the plan's §4.1 index? Completion of an FG task did
   not update the phase-matrix index. **Recommend a closing-process rule**: every
   completed FG must update `implementation_plan.md` §4.1 *and* `TASKS.md` before it is
   marked closed. This prevents recurrence and is the highest-value durable fix.

5. **Adversarial review of the design itself.**
   Detailed-design §16 mandates 案の敵対的review as a stage, but the repo has **no
   automated adversarial check** — it is manual doc review (this task). Is manual review
   sufficient? For a PoC/Pilot maturity, yes; but the plan should note that the
   adversarial review is currently a *human/reviewer* activity, not an enforced gate.

## 8. Brush-up (revisions from adversarial review)

- **Scope the STEP claim**: state that real B-Rep/STEP is produced only on the cadquery
  (native) path; the surrogate path emits placeholder STEP + simplified box STL. The
  viewer renders the STL mesh (geometrically equivalent). (Applied to `viewer.py` text.)
- **Demote CAD-FG-16** from "recommended" to "optional candidate" to avoid redundancy
  with DFM/AM (§5, §4.1 updated accordingly).
- **Add closing-process rule** (§9): every FG completion updates `implementation_plan.md`
  §4.1 + `TASKS.md` before closure. This directly fixes the drift root cause.
- **Keep deferred items explicitly gated** under `approval_required` with the named gate
  (`AGENTS.md` §4.2 for new DSL ops; human approval for production phases).
- **Note** the adversarial review of the design is a human/reviewer activity, not yet an
  enforced automated gate.

## 9. Closing-process rule (added by brush-up)

> When an `CAD-FG-*` task is closed, the closer MUST: (1) add/extend its row in
> `docs/cad_agent_implementation_plan.md` §4.1, and (2) record completion + commit in
> `TASKS.md`, before marking the task `completed`. This prevents the status-drift found
> in CAD-FG-15.

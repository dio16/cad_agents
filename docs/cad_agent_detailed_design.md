# CADAGENT Detailed Design

## 1. Document status
- Status: maintained; CAD-REVIEW-02 catch-up applied (2026-07-12)
- Source: `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`
- Related: `docs/cad_agent_catchup_detailed_design.md` (FG-18–22 catch-up design), `docs/backlog/IMPLEMENTATION_HISTORY.md` (completed tasks)
- Current maturity: PoC/Pilot validated; 288 pytest pass; topology honesty + E2E job runner + job store + export gate + LLM mock loop implemented

## 2. Executive summary

CADAGENT converts human design intent into structured engineering artifacts through deterministic CAD runtime and validation gates.

**Implemented (2026-07-12)**:

| Layer | Implementation |
|---|---|
| Requirement extraction | fixture + LLM adapter (mock default, CAD_AGENT_LLM_LIVE=1 for live) |
| Specification composition | fixture + LLM adapter (route_model enforced) |
| Parametric DSL | golden DSL + mechanism compiler (allowlist-based) |
| CAD Runtime | CadQuery/OCCT (native) + deterministic surrogate (fallback) |
| Validation | dimensions, artifact presence, DFM parameter_proxy, topology unchecked (honest null) |
| E2E Job Runner | fixture_pipeline / structured_pipeline / llm_pipeline modes |
| Job Store | sqlite3 durable (local_durable_stub), jobs/approvals/audit tables |
| Export gate | EXPORT_REQUIRES_NATIVE_KERNEL for surrogate kernel |
| Orchestrator | state machine + audit JSONL + max_revision_loops + approval gates |
| API server | stdlib HTTP (local skeleton), /v1/workflows/run, /v1/cad/jobs, /v1/exports |

**Deferred**: production deployment (K8s, Cosign), real worker pools, FEA, production auth, material DB/PLM/ERP/MES.

## 3. Goals and non-goals

### Goals

1. Convert natural-language design intent into `Requirement JSON`.
2. Convert requirements into human-reviewable `Specification JSON`.
3. Convert approved specifications into validated `Parametric DSL`.
4. Execute validated DSL through deterministic CAD Runtime.
5. Treat STEP / B-Rep as canonical geometry artifacts.
6. Treat STL / 3MF / glTF / PNG / PDF as derived artifacts.
7. Run schema, AST, geometry, DFM/AM, assembly, and motion validation where supported.
8. Escalate after repeated validation failures or approval-required changes.
9. Preserve traceability across prompts, models, specs, DSL, CAD artifacts, validation reports, and approvals.

### Non-goals for this pass

- Implement CAD features.
- Add native CAD workers.
- Add real LLM endpoints.
- Add production API services.
- Add `schemas/v1/*`, `cad_runtime/`, `dsl/`, or `validation/` implementation code.
- Replace existing PoC/Pilot contracts.
- Treat current repo maturity as production-ready.

### Future approved implementation scope

Future approved work may implement:

- Bounded Phase 1 hardening of the existing PoC/native CadQuery path.
- Native CAD Runtime with OCCT / FreeCAD / CadQuery integration.
- Deterministic DSL operation registry.
- Geometry, DFM/AM, assembly, and motion validation.
- Human approval workflow and revision loop.
- Artifact export and audit storage.

## 4. Source traceability

| Origen source section | Maintained design section | Notes |
|---|---|---|
| MVP scope and goals | Sections 3, 5, 14 | Current repo remains PoC/Pilot maturity. |
| System architecture | Section 6 | Design remains prompt/spec/DSL/CAD/Validation/Orchestrator pipeline. |
| CAD kernel selection | Section 8 | OCCT/CadQuery remains target; current repo uses deterministic surrogate paths. |
| LLM agent design | Sections 6, 9 | LLMs propose structured JSON/DSL only. |
| Mechanism DSL | Section 9 | DSL remains allowlist-gated and schema/AST validated. |
| CAD Runtime contract | Section 8 | Runtime must be deterministic and failure-transparent. |
| Validation contract | Section 10 | Validation remains the quality gate. |
| Orchestrator / approval workflow | Section 11 | Approval gates are mandatory for spec changes and export. |
| API / infrastructure | Sections 12, 13 | API and infrastructure are future approved implementation work. |
| Security / audit | Section 12 | Data classification and audit remain required. |

## 5. Current repository maturity

| Area | Current state | Design implication |
|---|---|---|
| Local CLI | Present | Use existing `run_cad_agent.sh` commands for validation. |
| Phase 1 PoC | Present | Requirement, Specification, Parametric DSL, Validation Report contracts exist. |
| Phase 1 PoC/native CadQuery path | Present and hardened | Use for validation and artifact-hash checks; production worker deployment remains future work. |
| Phase 2 Pilot | Present | DFM/AM profile, review diff, audit, and gateway probes exist. |
| Native CAD worker | Not guaranteed | Treat production native worker deployment as future work unless explicitly approved. |
| Production API service | Skeleton only | Do not present as production-ready. |
| LLM endpoints | Not integrated | Keep model routing as policy/design only. |
| Artifact store | Local PoC/Pilot artifacts | Future persistence remains separate. |

## 6. Architecture overview

```text
Human intent
  → Requirement Extractor
  → Requirement JSON (unknowns / assumptions separated)
  → Spec Composer
  → Specification JSON (human approval gate)
  → Mechanism Planner (design-intent; not yet implemented)
  → Mechanism plan
  → DSL Compiler (allowlisted DSL only)
  → Schema / AST validator
  → Parametric DSL
  → Deterministic CAD Runtime (security-policy API boundary)
  → STEP / B-Rep / derived artifacts
  → Validation
      → Assembly validation (parallel path)
      → Motion validation (parallel path)
  → Orchestrator (state machine; see Section 11)
  → Approval / revision / export

Security policy integration points:
  - API key enforcement (CAD_AGENT_API_KEY; default local-dev-key)
  - CORS headers on API responses
  - Audit / traceability recorded at every transition
```

### Component responsibilities

| Component | Input | Output | Responsibility |
|---|---|---|---|
| Requirement Extractor | Human intent, known context | Requirement JSON | Extract requirements, unknowns, assumptions |
| Spec Composer | Requirement JSON | Specification JSON | Draft engineering specs and approval needs |
| Mechanism Planner | Specification JSON | Mechanism plan | Propose mechanism structure |
| DSL Compiler | Mechanism plan | Parametric DSL | Generate allowlisted DSL only |
| CAD Runtime | Validated DSL | STEP / B-Rep / derived artifacts | Execute deterministic CAD operations |
| Validation | Spec + artifacts | Validation Report | Pass/fail with reason codes |
| Orchestrator | Pipeline state | Job state / revision requests | Gate, retry, escalate |
| Policy / Audit | Events | Audit log | Data classification, retention, traceability |
| Model Gateway | Route request | Selected model route | Apply routing policy |

## 7. Artifact ownership and正本 rules

| Artifact | Canonical status | Notes |
|---|---|---|
| `Requirement JSON` | Canonical requirement artifact | Must include unknowns and assumptions. |
| `Specification JSON` | Canonical design spec | Requires human approval before CAD generation. |
| `Parametric DSL` | Canonical CAD instruction | Must pass schema and AST validation. |
| STEP / B-Rep | Canonical geometry | Derived meshes must not replace this. |
| STL / 3MF | Derived print artifacts | Must come from validated geometry. |
| glTF / PNG / PDF | Derived review artifacts | Used for viewing and reporting. |
| Validation Report | Canonical quality record | Must include pass/fail and failures. |
| Audit log | Canonical event record | Append-style and traceable. |

## 8. Contract design

### JSON schema boundary

- All LLM outputs must be schema-valid before downstream use.
- Unknowns and assumptions must be separated.
- Approval-required fields must be explicit.
- Raw code, shell commands, and arbitrary Python must not be accepted as CAD input.

### DSL boundary

- DSL operations are allowlisted.
- Parameter references must resolve.
- Feature order must be executable.
- Unsupported operations must fail validation, not become raw code.
- New operations require human approval.

### Validation boundary

- Validation must return machine-readable reason codes.
- Failed artifacts must not be exported for print.
- Validation override requires reviewer approval.
- Three or more repeated failures require human review.

### Human approval boundary

Approval is required for:

- Specification freeze.
- Manufacturing profile changes.
- Material changes.
- Drive method changes.
- New DSL operations.
- Validation override.
- Print export.
- Regulated or export-controlled data handling.

## 9. CAD Runtime design

### Execution model

- CAD Runtime receives only validated DSL.
- Runtime maps DSL operations to deterministic CAD functions.
- Runtime records success/failure and artifact hashes.
- Runtime does not interpret human intent directly.

### Native vs surrogate boundary

| Mode | Allowed use | Notes |
|---|---|---|
| Native CAD | Approved Phase 1 PoC/native CadQuery path | OCCT / FreeCAD / CadQuery path for validated DSL; production worker deployment remains future scope. |
| Phase 1 hardening | Existing PoC/native CadQuery path | Export failures, z-only axes, parameter references, `step_ap242`, temp contract-test output, and artifact/hash metadata checks are hardened. |
| Deterministic surrogate | Current PoC/Pilot fallback | Records native availability and keeps validation meaningful when native executable is absent. |
| Raw code execution | Forbidden by default | Requires explicit approval and audit if ever allowed. |

### Error handling

Runtime failures must be classified, not hidden.

| Error class | Meaning |
|---|---|
| `UNSUPPORTED_DSL_OP` | Operation is not allowlisted. |
| `DSL_AST_VALIDATION_FAILED` | Schema or AST validation failed before CAD build. |
| `INVALID_PARAMETER_REFERENCE` | Parameter cannot be resolved. |
| `CAD_BUILD_FAILED` | CAD generation failed. |
| `BOOLEAN_FAILED` | Boolean operation failed. |
| `EXPORT_FAILED` | Artifact export failed. |
| `KERNEL_TIMEOUT` | Runtime exceeded time limit. |

## 10. Validation design

### Validation layers

| Layer | Purpose | Current maturity |
|---|---|---|
| Schema validation | JSON contract enforcement | Present in Phase 1. |
| AST validation | DSL operation and order validation | Present in Phase 1. |
| Geometry validation | B-Rep / mesh quality | PoC proxy; stronger validation future. |
| DFM/AM validation | Manufacturing profile checks | Pilot profile checks present. |
| Assembly validation | Part placement and interference | Future work beyond current stubs. |
| Motion validation | Rotational sweep and clearance | Future work. |

### Phase 1 hardening checks

Phase 1 hardening keeps the single-part PoC/native CadQuery path explicit and auditable:

- `derivative_outputs` must include `step_ap242`.
- Feature axes are restricted to z-only in both schema and AST checks.
- Parameter reference strings must resolve to numeric parameters.
- CadQuery STEP/STL export failures are surfaced as `EXPORT_FAILED` instead of being hidden.
- `phase1-contract-test` writes reports to a temporary directory, not to repository-local `reports/phase1_contract_test.json`.
- Artifact validation recomputes `sha256` hashes and verifies metadata includes `cad_kernel`.

### Validation report requirements

A validation report must include:

- Traceability ID.
- Specification ID.
- Artifact IDs.
- Check statuses.
- Reason codes.
- Failure locations.
- Overall pass/fail.
- Revision feedback when failed.

## 11. Orchestrator and human approval

### State model

```text
created
  → spec_pending_approval
  → spec_approved
  → dsl_generated
  → cad_built
  → validation_running
  → validation_passed
  → pending_export_approval
  → exported

failure path:
  → validation_failed
  → revision_requested
  → (resubmit spec) spec_pending_approval
  → cad_built
  → validation_running

escalation (terminal sink; reachable from any state that lists it):
  → escalated_to_human   (no automated recovery; human resolves out-of-band)
```

Transition table (implemented `Workflow` states):

| From | Allowed next states |
|---|---|
| created | spec_pending_approval, spec_approved, validation_failed, escalated_to_human |
| spec_pending_approval | spec_approved, revision_requested, escalated_to_human |
| spec_approved | dsl_generated, cad_built, validation_failed, revision_requested, escalated_to_human |
| revision_requested | spec_pending_approval, dsl_generated, validation_failed, escalated_to_human |
| dsl_generated | cad_built, revision_requested, escalated_to_human |
| cad_built | validation_running, revision_requested, escalated_to_human |
| validation_running | validation_passed, validation_failed, revision_requested, escalated_to_human |
| validation_passed | pending_export_approval, revision_requested, escalated_to_human |
| validation_failed | revision_requested, escalated_to_human |
| pending_export_approval | exported, revision_requested, escalated_to_human |
| exported | revision_requested, escalated_to_human |
| escalated_to_human | (none — terminal sink; human-in-the-loop resolution is handled out-of-band, not via the automated `Workflow` state machine) |

### Escalation conditions

- Three or more validation failures.
- Spec change required.
- New DSL operation required.
- Regulated or export-controlled data detected.
- Validation override requested.
- Print export requested before approval.

## 12. Security, compliance, and data routing

| Data class | Default route | Approval |
|---|---|---|
| Public | Commercial / hybrid / on-prem | Not required |
| Internal | Policy-defined commercial / hybrid | Policy-defined |
| Confidential | On-prem preferred | Required for exceptions |
| Regulated | On-prem | Human approval required |
| Export-controlled | On-prem | Legal/export review required |

Security rules:

- Treat prompt injection as expected.
- Keep external content separate from system instructions.
- Do not send confidential data to commercial routes without approval.
- Keep audit records for model route, data classification, and retention.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| LLM changes spec without approval | Human approval gate and audit log |
| DSL becomes raw code | Allowlist and AST validation |
| Surrogate mistaken for native CAD | Explicit mode metadata and validation evidence |
| Validation is too weak | Reason codes, profile rules, and future stronger checks |
| Motion/assembly failures are missed | Future motion and assembly validation gates |
| Production skeleton mistaken for production | Maturity labels in all planning docs |
| Audit trail is incomplete | Append-style JSONL and traceability IDs |

## 14. Acceptance criteria

### For this design document

- It is derived from the Origen CADAGENT source.
- It separates current repo maturity from future implementation.
- It defines responsibility boundaries, artifact ownership, validation, approval, and security.
- It avoids stale validation terms.
- It is included in maintained doc validation.

### For bounded Phase 1 hardening

- Existing PoC/native CadQuery behavior is hardened without production deployment.
- Export failures, z-only axes, parameter references, `step_ap242`, temp contract-test output, and artifact/hash metadata checks are documented.
- Phase 1 validation commands pass.

### For future approved CADAGENT implementation

- Requirement JSON is generated and schema-validated.
- Specification JSON is human-approved before CAD generation.
- Parametric DSL is schema and AST validated.
- CAD Runtime generates STEP / B-Rep artifacts.
- Validation Report records pass/fail and reason codes.
- Human approval is recorded before print export.
- Audit log preserves traceability.

## 15. Glossary / terminology normalization

| Preferred term | Meaning |
|---|---|
| `gyro kinetic object` | Initial multi-axis kinetic object target. |
| `gyro_kinetic_v1` | First target planning label. |
| `kinetic object v1` | Human-readable first target label. |
| `deterministic surrogate` | Current PoC/Pilot fallback when native executables are absent. |
| `native CAD` | Approved Phase 1 PoC/native CadQuery path; production worker deployment remains future scope. |
| `Phase 1 hardening` | Bounded hardening of the existing PoC/native CadQuery path, not production deployment. |

## 16. End-to-end workflow and HTML review artifact

The end-to-end design/review flow is:

```text
構想 → 詳細設計 → 設計案review → 案の敵対的review → 実装計画作成 → 実装 → テストケースでテスト
```

Mapped to the orchestrator workflow (`docs/ORCHESTRATOR_WORKFLOW.md`):

- 構想 / 詳細設計 → Requirement / Specification JSON with human approval gate.
- 設計案review / 案の敵対的review → the assembled result is reviewed by the human/reviewer using the **standard HTML assembly viewer** (`src/cad_agent/viewer.py`, `write_assembly_viewer`), driven by `run_assembly_pipeline` in `src/cad_agent/platform_poc.py`. The viewer is emitted by default into the artifact directory so a human can visually confirm the Assy result (surrogate AABB boxes; true gear teeth require a new approved DSL operation).
- 実装計画作成 → plan under `docs/cadagent_plans/<TASK_ID>/implementation-plan.md`.
- 実装 / テストケースでテスト → deterministic CAD runtime, Validation, and `examples/*` test cases.

This viewer is the standard human-review artifact for assemblies; it closes the gap where placeholder STEP / box STL could not be visually verified by a human.

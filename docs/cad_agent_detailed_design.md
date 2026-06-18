# CADAGENT Detailed Design

## 1. Document status

- Status: maintained planning/design artifact
- Source: `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`
- Related prompt workflow: `docs/prompt_execution_plan.md`
- Scope boundary: this document defines CADAGENT design intent and maintained planning contracts. It does not implement CAD features, native workers, schemas, API services, LLM endpoints, or production architecture.

## 2. Executive summary

CADAGENT is an AI-assisted mechanical design platform that converts human design intent into structured engineering artifacts, then uses deterministic CAD runtime and validation components to generate and verify geometry.

The core design principle is separation of responsibility:

| Layer | Responsibility | Must not do |
|---|---|---|
| Human | Final intent, approval, specification changes | Delegate safety/legal judgment to agents |
| LLM agents | Requirement, specification, mechanism, and DSL proposals | Execute raw CAD code or change approved specs alone |
| Deterministic CAD Runtime | Execute validated DSL and generate geometry/artifacts | Interpret specs or hide failures |
| Validation | Geometry, manufacturing, assembly, and motion quality gates | Mark failed artifacts as pass |
| Orchestrator / Audit | Workflow, revision loop, approval, traceability | Bypass gates or omit audit records |

This pass creates planning/design documents only. Future implementation must remain gated by review and validation.

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
| Phase 1 PoC/native CadQuery path | Present | Use for validation and artifact-hash checks; production worker deployment remains future work. |
| Phase 2 Pilot | Present | DFM/AM profile, review diff, audit, and gateway probes exist. |
| Native CAD worker | Not guaranteed | Treat production native worker deployment as future work unless explicitly approved. |
| Production API service | Skeleton only | Do not present as production-ready. |
| LLM endpoints | Not integrated | Keep model routing as policy/design only. |
| Artifact store | Local PoC/Pilot artifacts | Future persistence remains separate. |

## 6. Architecture overview

```text
Human intent
  → Requirement Extractor
  → Requirement JSON
  → Spec Composer
  → Specification JSON
  → Mechanism Planner
  → Mechanism plan
  → DSL Compiler
  → Parametric DSL
  → Schema / AST validator
  → Deterministic CAD Runtime
  → STEP / B-Rep / derived artifacts
  → Validation
  → Orchestrator
  → Approval / revision / export
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
| Deterministic surrogate | Current PoC/Pilot fallback | Records native availability and keeps validation meaningful when native executable is absent. |
| Raw code execution | Forbidden by default | Requires explicit approval and audit if ever allowed. |

### Error handling

Runtime failures must be classified, not hidden.

| Error class | Meaning |
|---|---|
| `UNSUPPORTED_DSL_OP` | Operation is not allowlisted. |
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
  → requirement_extracted
  → spec_drafted
  → pending_spec_approval
  → spec_approved
  → mechanism_planned
  → dsl_generated
  → cad_built
  → validation_running
  → validation_passed
  → pending_export_approval
  → exported
```

Failure path:

```text
validation_failed
  → revision_requested
  → dsl_revised
  → cad_built
  → validation_running
```

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

# Mechanism DSL v1

## Status
Phase 0 contract only. No implementation.

## Purpose
Define the allowlist-first Mechanism DSL contract for the first CADAGENT implementation pass. The DSL is the only permitted route from LLM output to CAD Runtime.

## Source traceability
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:254-360`
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:782-799`
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:967-997`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:304-487`

## In scope
- Phase 1 schema boundary: Requirement JSON, Specification JSON, Parametric DSL, Validation Report.
- Units fixed to `mm`.
- Parameter references must resolve to the approved parameter table.
- Feature order must be executable: base geometry before cuts/holes and before derivative outputs.
- Allowed v1 operations: `box`, `cylinder`, `through_hole`; Task 06.2 adds bounded `shaft` approval.
- Deterministic surrogate behavior is recorded when native CadQuery is absent.
- Derivative outputs are declared as metadata only and do not grant raw code execution.

## Out of scope / deferred
- Deferred v2/future operations include `fillet`, `chamfer`, `loft`, `sweep`, patterns, assembly placement, mates, joints, gear generators, bearing seats, gimbal rings, and motion sweep checks.
- Task 06.2 approves the minimal `shaft` mechanism operation set documented in `MECHANISM_DSL_OPERATIONS.md`; all other mechanism-specific operations remain future contract work.
- Forbidden without separate approval: unsupported DSL operations, raw Python/CadQuery code, shell commands, arbitrary imports, arbitrary file access, network access, and production artifact export from surrogate CAD.
- API endpoint schemas, native worker pool code, and example artifacts are not part of this contract pass.

## Contract summary
Mechanism DSL v1 is an allowlist-first, schema-validated operation graph. LLMs may generate only Parametric DSL that references approved parameters and operations. The PoC allowlist is exactly `box`, `cylinder`, and `through_hole`. Unsupported operations produce `UNSUPPORTED_DSL_OP` or an equivalent contract failure path and must not be implemented by raw code. Task 06.2 adds a bounded deterministic `shaft` mechanism operation documented in `MECHANISM_DSL_OPERATIONS.md`; other mechanism-specific operations remain future contract work.

## Acceptance criteria
- `units` is `mm` for every accepted Parametric DSL.
- Every parameter reference resolves to the Specification JSON parameter table.
- Feature order is statically executable.
- Only `box`, `cylinder`, `through_hole`, and the approved `shaft` operation are allowed for this branch.
- `derivative_outputs` are declared without changing canonical artifact ownership.
- New operations require human/reviewer approval and a contract update before use.

## Open decisions / deferred decisions
- Exact JSON field names remain tied to the approved Phase 1 schema boundary.
- Assembly, motion, gear, and bearing DSL operations are deferred to future approved contracts.
- Surrogate artifact labeling and native promotion rules are governed by `CAD_RUNTIME_CONTRACT.md`.
- Future operation governance must define versioning, compatibility, and validation impact before approval.

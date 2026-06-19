# Validation Contract

## Status
Phase 0 contract only. No implementation.

## Purpose
Define Validation as a quality gate that reports pass/fail, reason codes, and escalation needs. Validation does not approve design changes.

## Source traceability
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:415-475`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:304-487`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:530-573`

## In scope
- Validation layers: schema, CAD geometry, manufacturing profile, assembly proxy, and motion/future checks.
- Current maturity: bbox, volume, topology proxy, unit consistency, DFM-AM rules, z-only feature axes, parameter-reference resolution, and export failure propagation.
- Current PoC checks: `schema_check`, `unit_check`, `parameter_check`, `feature_order_check`, `axis_check`, `parameter_reference_check`, `brep_validity_check`, `mesh_watertight_check`, `dfm_fdm_check`, `export_check`.
- Future contracted checks: `assembly_clearance_check`, `motion_axis_check`, `motion_sweep_collision_check`, `gear_mesh_check`, `export_check`.
- Reason codes must identify the failed check and the deterministic rule that failed.
- Validation Report is passed to the Orchestrator and Revision Agent.

## Out of scope / deferred
- Full native B-Rep healing, self-intersection analysis, contact analysis, FEA, precision assembly validation, and certified manufacturing approval.
- Validation override authority.
- Failed-to-pass rewrites, approval substitution, or hiding failed checks.
- API endpoint schemas and production validation service implementation.

## Contract summary
Validation is a gate, not an approval authority. A failed check remains failed even if a reviewer later grants a conditional override. The report must preserve the original failure, reason code, context, and override metadata. Current PoC/Pilot validation is intentionally limited to bbox, volume, topology proxy, unit consistency, and DFM-AM rules.

## Acceptance criteria
- Validation receives Specification JSON, Parametric DSL, CAD artifacts, metadata, and manufacturing profile context.
- Each check returns pass/fail with a reason code and human-readable explanation.
- Failed checks are never rewritten as pass.
- Validation override is reviewer/human approval only and remains conditional.
- Three or more validation failures escalate to `needs_human_review`.
- Future checks are clearly marked as deferred or not executed.

## Open decisions / deferred decisions
- Exact numeric thresholds for future profiles are deferred.
- FEA, motion sweep, gear mesh, and full assembly validation are future maturity targets.
- Override UI/API contracts are future work.
- Long-term immutable audit storage is future scope.

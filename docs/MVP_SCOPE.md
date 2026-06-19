# MVP Scope

## Status
Phase 0 contract only. No implementation.

## Purpose
Define the contract MVP for the first CADAGENT implementation pass. This MVP is a bounded design and validation target, not a production platform release.

## Source traceability
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:13-89`
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:530-590`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:3-65`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:121-190`

## In scope
- Contract scope for a 3D-printable, non-safety-critical, desktop-size, low-speed kinetic mechanism.
- First target object: `gyro_kinetic_v1`, a gyro kinetic object / kinetic object v1.
- Multiple-part assembly with visible low-speed rotation, printable parts, bearings, shafts, and M2/M3 fasteners.
- Manufacturing profiles: `fdm_standard` and optional `sla_high_precision`.
- Canonical artifacts: Requirement JSON, Specification JSON, Parametric DSL, Validation Report, STEP/B-Rep.
- Derived artifacts: STL, 3MF, glTF/GLB, PNG, and simple PDF review report.
- Human approval boundaries for spec freeze, manufacturing profile changes, validation override, regulated/export-controlled tags, and print export.

## Out of scope / deferred
- Production API service, native worker pool, real LLM endpoint, PLM/ERP/MES integration.
- Safety-critical, regulated, export-controlled, medical, vehicle, aircraft, or human-protection use.
- Real watch accuracy, long-life durability guarantees, high-speed rotation, escapement, spring barrel, and full motion/FEA certification.
- Commercial-CAD-level freeform surfacing and fully automatic manufacturing approval.
- `schemas/v1/*`, `cad_runtime/`, `dsl/`, `validation/`, and example artifacts are not created by this contract pass.

## Contract summary
The MVP is a contract MVP: it fixes what the first implementation pass must support and what remains future work. The first object is `gyro_kinetic_v1`, a low-speed gyro kinetic object for visual motion and printability validation, not a functional timepiece. The v1 Mechanism DSL is intentionally narrower than the full `gyro_kinetic_v1` mechanism; mechanism-specific operations require later approved contract updates. Phase 1 PoC/native CadQuery golden path is approved for validated STEP/STL generation and artifact-hash recording; deterministic surrogate recording remains a PoC fallback when native CadQuery is absent, and production native worker deployment remains future scope.

## Acceptance criteria
- The five Phase 0 contract documents exist and follow the approved template.
- MVP scope is explicitly marked as contract-only and non-production.
- `gyro_kinetic_v1` is described using approved terminology.
- Canonical and derived artifact boundaries are explicit.
- Manufacturing profiles and approval boundaries are listed.
- No implementation code, schema files, API endpoint schemas, native worker pool, or example artifacts are added.

## Open decisions / deferred decisions
- Exact `gyro_kinetic_v1` dimensions and part count remain subject to approved Specification JSON.
- SLA profile thresholds are deferred unless a reviewer approves a pilot profile.
- Gear, bearing, motion sweep, and FEA checks are future validation extensions.
- Production deployment, multi-tenant storage, and real worker pools are future scope.

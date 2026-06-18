# CAD Runtime Contract

## Status
Phase 0 contract only. No implementation.

## Purpose
Define the contract boundary between validated Parametric DSL and deterministic CAD artifact generation.

## Source traceability
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:365-412`
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:627-688`
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:693-732`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:3-65`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:530-573`

## In scope
- Accept only schema-validated Parametric DSL as input.
- Native path: CadQuery/OCCT generation when available.
- Deterministic surrogate path: record surrogate behavior when native CadQuery is absent.
- Canonical artifacts: STEP / B-Rep.
- Derived artifacts: STL, 3MF, glTF/GLB, PNG, PDF review report.
- Metadata expectations: traceability IDs, source spec/dsl/report references, runtime mode, artifact hash, timestamp, and surrogate/native status.
- V1/runtime error codes: `CAD_BUILD_FAILED`, `UNSUPPORTED_DSL_OP`, `INVALID_PARAMETER_REFERENCE`, `NON_POSITIVE_VOLUME`, `BOOLEAN_FAILED`, `KERNEL_TIMEOUT`, `EXPORT_FAILED`.
- Reserved future error codes: `FILLET_FAILED`, `GEAR_GENERATION_FAILED`, `ASSEMBLY_CONSTRAINT_FAILED`.

## Out of scope / deferred
- Production worker pool, production API service, real LLM endpoint, and API endpoint schema files.
- Raw code execution, arbitrary imports, arbitrary file access, and network access.
- Surrogate STEP as production artifact.
- Native FreeCAD/OCCT/Blender workers, FEA, motion sweep, and full assembly export are future work.

## Contract summary
CAD Runtime is the deterministic executor. It never interprets free text, never executes LLM-generated raw code, and never bypasses Validation. If native CadQuery is absent, it records deterministic surrogate behavior for PoC/Pilot maturity and marks generated artifacts accordingly. Native STEP/B-Rep remains the canonical artifact boundary; surrogate output is not promoted to production artifact status without explicit approval.

## Acceptance criteria
- CAD Runtime accepts only validated Parametric DSL.
- Native and surrogate modes are explicitly distinguished in metadata.
- Artifact hashes are recorded for canonical and derived artifacts.
- Unsupported DSL operations return machine-readable errors.
- No raw code, arbitrary imports, arbitrary file access, or network access is permitted.
- Audit log entries include input/output references, runtime mode, error codes, and artifact hashes.

## Open decisions / deferred decisions
- Exact sandbox mechanism is deferred; policy requires network isolation, bounded I/O, and resource/time limits.
- Native promotion criteria for surrogate-to-production artifacts are deferred.
- Full B-Rep validity, mesh watertightness, assembly export, and motion sweep export are future implementation concerns.
- Production deployment architecture remains future scope.

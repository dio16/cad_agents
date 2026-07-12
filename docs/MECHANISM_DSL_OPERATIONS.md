# Mechanism DSL Approved Operations

Status: approved for CAD-P06 Task 06.2, extended by CAD-FG-17 (tourbillon support).

This document records the small deterministic mechanism operation set that the
Phase 1 compiler may accept before any LLM/raw-code path is introduced.

## Approved operations

| Mechanism-plan operation | Phase 1 Parametric DSL mapping |
|---|---|
| `shaft` | one `cylinder` feature with generated numeric `radius` and `length` parameters |

## Approved direct Parametric DSL operations (CAD-FG-17)

The following operations were approved (with the tourbillon condition: the
additional DSL must include every element needed to build a tourbillon object)
and added to `ALLOWED_DSL_OPERATIONS` in `dsl_compiler.py` and
`ALLOWED_DSL_OPS` in `platform_poc.py`. All are z-axis extrusions and reuse the
existing contract (`units = mm`, `$param` references, `axis = "z"`,
`positions_mm`).

| Operation | Required fields | Optional fields | Purpose |
|---|---|---|---|
| `gear` | `module_mm`, `teeth`, `thickness_mm`, `bore_diameter_mm` | — | Toothed wheel (involute-style spur approximation) |
| `escape_wheel` | `teeth`, `tip_radius_mm`, `thickness_mm`, `bore_diameter_mm` | `tooth_type` (`pointed`\|`club`) | Escapement star wheel |
| `balance_wheel` | `outer_diameter_mm`, `rim_width_mm`, `spokes`, `thickness_mm`, `bore_diameter_mm` | — | Oscillating wheel with rim + spokes |
| `lever` | `length_mm`, `width_mm`, `thickness_mm`, `fork_width_mm`, `pivot_diameter_mm` | — | Pallet fork / lever with pivot bore |
| `cage` | `outer_diameter_mm`, `arm_count`, `thickness_mm`, `bore_diameter_mm` | `bridge` (bool, default `true`) | Rotating carriage that carries the escapement |
| `hairspring` | `outer_diameter_mm`, `coils`, `wire_diameter_mm`, `thickness_mm` | — | Spiral balance spring (Archimedean band) |
| `jewel` | `diameter_mm`, `thickness_mm` | — | Bearing jewel / pivot stone |

Failure to satisfy the required fields is rejected by the Phase 1 validator
(`_validate_phase1_feature`) before any CAD runtime call. Generation failures
during geometry build surface the reserved contract code `GEAR_GENERATION_FAILED`.

## `shaft` mapping

Required numeric inputs:

- `diameter_mm`
- `length_mm`

Generated DSL:

```json
{
  "units": "mm",
  "traceability_id": "tr_dsl_shaft_<deterministic-hash-or-plan-id>",
  "parameters": {
    "radius": "<diameter_mm / 2>",
    "length": "<length_mm>"
  },
  "features": [
    {
      "op": "cylinder",
      "radius_mm": "$radius",
      "height_mm": "$length",
      "axis": "z",
      "positions_mm": [[0, 0]]
    }
  ],
  "derivative_outputs": ["step_ap242"]
}
```

The emitted `traceability_id` is always schema-valid for the Phase 1
Parametric DSL schema. If the mechanism plan already contains a valid
`tr_dsl_*` ID, the compiler preserves it; otherwise it emits a deterministic
`tr_dsl_shaft_<hash>` ID.

A string beginning with `$` is treated as a reference to an existing numeric
parameter. If the referenced parameter is absent or non-numeric, compilation
fails with `INVALID_PARAMETER_REFERENCE`. `positions_mm` must be a non-empty
array of two-number coordinate pairs; otherwise compilation fails with
`INVALID_POSITIONS_MM`.

## Explicitly not approved

The following remain rejected until a later task updates this document and the
compiler allowlist:

- bearing seats
- bearing rings
- motion constraints
- FEA
- raw code execution
- arbitrary LLM-generated DSL fragments

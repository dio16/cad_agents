# Mechanism DSL Approved Operations

Status: approved for CAD-P06 Task 06.2 only.

This document records the small deterministic mechanism operation set that the
Phase 1 compiler may accept before any LLM/raw-code path is introduced.

## Approved operations

| Mechanism-plan operation | Phase 1 Parametric DSL mapping |
|---|---|
| `shaft` | one `cylinder` feature with generated numeric `radius` and `length` parameters |

## `shaft` mapping

Required numeric inputs:

- `diameter_mm`
- `length_mm`

Generated DSL:

```json
{
  "units": "mm",
  "traceability_id": "<plan.traceability_id or tr_dsl_mechanism>",
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

A string beginning with `$` is treated as a reference to an existing numeric
parameter. If the referenced parameter is absent or non-numeric, compilation
fails with `INVALID_PARAMETER_REFERENCE`.

## Explicitly not approved

The following remain rejected until a later task updates this document and the
compiler allowlist:

- bearing seats
- bearing rings
- cages
- gears and tooth geometry
- motion constraints
- FEA
- raw code execution
- arbitrary LLM-generated DSL fragments

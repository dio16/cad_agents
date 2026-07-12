# Gear Train Test Case (gear_train_v1)

A test case exercising the CAD-AGENT pipeline on a **1:10 parallel-axis compound gear train**
built from two distinct gear types.

## Design

- Stage 1 (spur):    pinion 20T → gear 40T   → ratio 2:1
- Stage 2 (helical): pinion 20T → gear 100T  → ratio 5:1
- Total = 2 × 5 = **10:1**, all three shaft axes parallel (z).
- Module = 2.0 mm. Center distances: stage1 = 60 mm, stage2 = 120 mm.

## How it maps to the surrogate

The framework's Mechanism DSL allowlist is `box`, `cylinder`, `through_hole` + `shaft`.
**`gear` is not an approved operation** (see `docs/MECHANISM_DSL_V1.md`,
`docs/MECHANISM_DSL_OPERATIONS.md`), so each gear blank is modeled as a `cylinder` on a
parallel z-axis. The 1:10 ratio is realized by the pitch radii; meshing pairs are
adjacent in the AABB check, all other pairs are separated along z.

## Run

```
uv run python examples/gear_train_v1/run_test.py
```

This validates the Requirement/Specification JSON against their schemas, runs each
Parametric DSL through `run_cad_runtime` (deterministic surrogate STEP/STL), runs the
assembly AABB interference check, and asserts the 1:10 ratio. Output:
`gear_train_validation_report.json`.
- The HTML assembly viewer is written to `artifacts/gear_train_v1/assembly_viewer.html` (the artifact directory, same place as the generated STEP/STL). Each part is rendered from its `run_cad_runtime` STL mesh (the artifact's actual geometry), placed at the assembly location.

## Limitations

- Surrogate geometry is simplified cylinders; no involute tooth geometry.
- True gear CAD requires a new approved `gear` DSL operation (human/reviewer approval + contract update).
- Surrogate STEP is a text placeholder; STL is a simplified box mesh (see `docs/CAD_RUNTIME_CONTRACT.md`).

# Gear Train Test Case v2 — changed dimensions

A second gear-train surrogate test case that reuses the deterministic CAD pipeline but
with **different dimensions** from `gear_train_v1`, to exercise the assembly viewer and
placement logic on new geometry.

## Design (1:10 parallel-axis compound train)

| Part | Type | Teeth (T) | Pitch radius r (mm) | Thickness (mm) | Shaft x (mm) | z-range (mm) |
|------|------|-----------|---------------------|----------------|--------------|--------------|
| pinion1 | spur   | 10 | 10 | 12 | 0  | 0–12  |
| gear1   | spur   | 25 | 25 | 12 | 35 | 0–12  |
| pinion2 | helical| 12 | 12 | 8  | 35 | 40–48 |
| gear2   | helical| 48 | 48 | 8  | 95 | 40–48 |

- Stage 1 ratio = 25/10 = 2.5; Stage 2 ratio = 48/12 = 4; total = **10:1**.
- Center distances: stage 1 = 10 + 25 = 35 mm; stage 2 = 12 + 48 = 60 mm.
- Shaft axes at x = 0, 35, 95.

## Run

```bash
uv run python examples/gear_train_v2/run_test.py
```

This validates the Requirement/Specification JSON against their schemas, runs each
Parametric DSL through `run_cad_runtime` (deterministic surrogate STEP/STL), runs the
assembly AABB interference check, and asserts the 1:10 ratio. Output:
`gear_train_validation_report.json`.

- The HTML assembly viewer is written to `artifacts/gear_train_v2/assembly_viewer.html` (the artifact directory, same place as the generated STEP/STL). Each part is rendered from its `run_cad_runtime` STL mesh (the artifact's actual geometry), placed at the assembly location — so the changed dimensions/placement above are reflected directly in the viewer.

## Limitations

- Surrogate geometry is simplified cylinders; no involute tooth geometry.
- True gear CAD requires a new approved `gear` DSL operation (human/reviewer approval + contract update).
- Surrogate STEP is a text placeholder; STL is a simplified box mesh (see `docs/CAD_RUNTIME_CONTRACT.md`).

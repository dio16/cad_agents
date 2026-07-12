# Tourbillon example (CAD-FG-17)

Demonstrates the **approved Mechanism DSL** needed to build an object with a
**tourbillon** (rotating carriage) mechanism. The additional DSL operations
approved for this task are:

| Operation | Purpose |
|-----------|---------|
| `gear` | Fixed fourth wheel / toothed wheel (involute-style spur approximation) |
| `escape_wheel` | Escapement star wheel (`tooth_type`: `pointed` | `club`) |
| `balance_wheel` | Oscillating wheel with rim + spokes |
| `lever` | Pallet fork / lever with fork and pivot bore |
| `cage` | Rotating carriage that carries the escapement (`bridge`: bool) |
| `hairspring` | Spiral balance spring (Archimedean band) |
| `jewel` | Bearing jewel / pivot stone |

All operations are z-axis extrusions and re-use the existing contract
(`units = mm`, `$param` references, `axis = "z"`, `positions_mm`).

## Run

```bash
uv run python examples/tourbillon/run_test.py
```

This:

1. Validates `requirement.json` and `specification.json` against their schemas.
2. Generates every part with the deterministic (cadquery) CAD runtime, emitting
   real STEP (AP242) + STL artifacts.
3. Runs the assembly pipeline (AABB interference check) and emits the standard
   HTML viewer (`artifacts/tourbillon/assembly_viewer.html`).
4. Runs `check_tourbillon_constraints`, which verifies the rotating `cage`
   physically contains its carried `escape_wheel` / `balance_wheel` (a violation
   surfaces the reserved `ASSEMBLY_CONSTRAINT_FAILED` contract code).
5. Writes `tourbillon_validation_report.json` and prints the summary.

Geometry note: the parts are stacked in distinct z-slabs so that each touches
(but does not overlap) its neighbour, which keeps the surrogate AABB interference
check clean for the nested tourbillon layout. The viewer renders the exact STL
mesh for every part placed at its assembly location.

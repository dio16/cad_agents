# Tourbillon 3D‑printable display object (examples/tourbillon_3dp)

Approximately 100 × 100 × 100 mm tourbillon mechanism designed for FDM
3D printing. Every part is produced by the deterministic (cadquery) CAD runtime
using the approved Mechanism DSL tourbillon operations.

## Mechanical honesty

**What is mechanically validated:**
- `fixed_wheel` (m=3, z=20) and `intermediate_wheel` (m=3, z=12) are placed at
  the correct centre distance of 48 mm — they *would* mesh if printed with
  proper tolerances. This is verified by `check_gear_mesh()`.
- The `cage` (⌀ 110 mm) physically contains the `escape_wheel` and
  `balance_wheel` — verified by `check_tourbillon_constraints()`.
- Every part geometry is real cadquery B‑Rep (STEP AP242) / STL, not a
  surrogate placeholder.

**What is display‑only (not mechanically functional):**
- The cage does not rotate; there is no bearing or axle simulation.
- The escape wheel, balance wheel, lever, and hairspring are positioned for
  visual display of the tourbillon layout. Their pivots and clearances are
  not validated against real escapement dynamics.
- The AABB interference check flags the `fixed_wheel↔intermediate_wheel`
  overlap — this is *expected* for meshing gears sharing a z‑slab and is
  documented in the output.

## Run

```bash
uv run python examples/tourbillon_3dp/run_all.py
```

## Output

All artifacts land in `artifacts/tourbillon_3dp/`:

| File | Description |
|---|---|
| `base/` | Solid base plate (100 × 100 × 10 mm) |
| `fixed_wheel/` | Fixed fourth wheel (m=3, 20 T, pitch‑r=30 mm) |
| `intermediate_wheel/` | Intermediate wheel meshing with fixed wheel (m=3, 12 T, pitch‑r=18 mm, cd=48 mm) |
| `cage/` | Rotating carriage (⌀ 110 mm, 5 arms, bridged) |
| `escape_wheel/` | Escapement star wheel (12 T, club tooth) |
| `balance_wheel/` | Balance wheel (⌀ 52 mm, 5 spokes) |
| `lever/` | Pallet fork (48 mm long) |
| `hairspring/` | Archimedean spiral spring (⌀ 38 mm, 8 coils) |
| `jewel/` | Bearing jewel (⌀ 8 mm) |
| `tourbillon_assembly.step` | Combined assembly STEP (all parts at display positions) |
| `tourbillon_assembly.stl` | Combined assembly STL |
| `assembly_viewer.html` | Interactive HTML viewer (self‑contained) |

## Validation output

```
Gear mesh: pass
  fixed_wheel (z=20) ↔ intermediate_wheel (z=12): centre distance = 48.0 mm ✓
Tourbillon containment: pass
Mechanical validation (gear mesh + tourbillon containment): pass
```

## Design notes

- Parts are stacked in distinct z‑slabs with 2 mm visual gaps; the two meshing
  gears share a z‑slab so their tooth profiles overlap (this is reported as
  expected AABB interference).
- Recommended print orientation: base flat, wheels face‑up, hairspring flat.
- Print with 0.2 mm layer height; no supports needed for most parts (the
  hairspring may benefit from a brim).

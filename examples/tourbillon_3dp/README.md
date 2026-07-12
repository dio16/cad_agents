# Tourbillon 3D‑printable display object (examples/tourbillon_3dp)

Approximately 100 × 100 × 100 mm tourbillon mechanism designed for FDM
3D printing. Every part is produced by the deterministic (cadquery) CAD runtime
using the approved Mechanism DSL tourbillon operations.

## Run

```bash
uv run python examples/tourbillon_3dp/run_all.py
```

## Output

All artifacts land in `artifacts/tourbillon_3dp/`:

| File | Description |
|---|---|
| `base/tr_dsl_3dp_base.stl` | Solid base plate (100 × 100 × 10 mm) |
| `fixed_wheel/tr_dsl_3dp_fixed_wheel.stl` | Fixed fourth wheel (spur gear, m = 3, 20 T) |
| `cage/tr_dsl_3dp_cage.stl` | Rotating carriage (⌀ 110 mm, 5 arms, bridged) |
| `escape_wheel/tr_dsl_3dp_escape_wheel.stl` | Escapement star wheel (12 T, club tooth) |
| `balance_wheel/tr_dsl_3dp_balance_wheel.stl` | Balance wheel (⌀ 52 mm, 5 spokes) |
| `lever/tr_dsl_3dp_lever.stl` | Pallet fork (48 mm long, 12 mm fork) |
| `hairspring/tr_dsl_3dp_hairspring.stl` | Archimedean spiral spring (⌀ 38 mm, 8 coils) |
| `jewel/tr_dsl_3dp_jewel.stl` | Bearing jewel (⌀ 8 mm) |
| `tourbillon_assembly.step` | Combined assembly STEP (all parts at display positions) |
| `tourbillon_assembly.stl` | Combined assembly STL |
| `assembly_viewer.html` | Interactive HTML viewer (self‑contained) |

## Design notes

- Parts are stacked in distinct z‑slabs with 2 mm visual gaps.
- The cage (⌀ 110 mm) contains the escape wheel and balance wheel; containment
  is verified by `check_tourbillon_constraints`.
- Print each STL separately; the assembly STEP/STL shows the intended layout
  for reference.
- Recommended print orientation: base flat, wheels face‑up, hairspring flat.

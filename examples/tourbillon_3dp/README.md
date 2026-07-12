# Tourbillon 3D‑printable display object (examples/tourbillon_3dp)

Approximately 100 × 100 × 100 mm tourbillon mechanism designed for FDM 3D printing.
Every part is produced by the deterministic (cadquery) CAD runtime using the approved
Mechanism DSL tourbillon operations.

## Mechanical validation

The `check_tourbillon_mechanics()` composite check validates:

| Check | Description | Result |
|---|---|---|
| Shaft clearance | Cage bore (⌀14 mm) accommodates central pivot shaft (⌀10 mm) with 4 mm radial clearance | ✓ |
| Gear mesh | `fixed_wheel` (m=3, z=20) ↔ `escape_pinion` (m=3, z=6) at correct centre distance 39 mm | ✓ |
| Cage containment | `escape_wheel` and `balance_wheel` fit within the cage outer radius of 55 mm | ✓ |

**Mechanically honest**: the gears would mesh if printed with proper tolerances.

**Display‑only**: the cage does not rotate; no escapement dynamics, bearing, or hairspring
torque simulation.

## Run

```bash
uv run python examples/tourbillon_3dp/run_all.py
```

## Output

| File | Description |
|---|---|
| `base/` | Base plate 100 × 100 × 10 mm |
| `fixed_wheel/` | Fixed fourth wheel (m=3, z=20, ⌀66 mm) |
| `escape_pinion/` | Escape pinion meshing with fixed wheel (m=3, z=6, cd=39 mm) |
| `cage/` | Rotating carriage (⌀110 mm, 5 arms, bridged) |
| `escape_wheel/` | Escapement star wheel (12 T, club tooth) |
| `balance_wheel/` | Balance wheel (⌀52 mm, 5 spokes) |
| `lever/` | Pallet fork |
| `hairspring/` | Archimedean spiral (⌀38 mm, 8 coils) |
| `jewel/` | Bearing jewel (⌀8 mm) |
| `tourbillon_assembly.step` | Combined assembly STEP |
| `tourbillon_assembly.stl` | Combined assembly STL |
| `assembly_viewer.html` | Interactive HTML viewer |

Individual STL+STEP files per part are in subdirectories.

# Tourbillon V21 Fabrication Package

This package is generated from `manifests/tourbillon_v21_onshape_run.json`.

## Status

- Fallback transform motion and Onshape pose snapshots are verified.
- Native Onshape Gear Relation is not verified and remains blocked in disposable probes.
- Hardware-in-context audit passes with 0 failures.

## Printed Parts

| Role | STL | STEP Source | Orientation Note |
| --- | --- | --- | --- |
| fixed_base | `stl/fixed_base.stl` | `/home/diobrando/cad/tourbillon/tourbillon_v20_step/01_base_608zz_bearing_pocket_v20.step` | Print flat on bottom face; bearing pocket upward; no support expected for vertical bores. |
| fixed_ring | `stl/fixed_ring.stl` | `/home/diobrando/cad/tourbillon/tourbillon_v20_step/02_fixed_internal_ring_clearance_teeth_v20.step` | Print flat on standoff-contact face; gear teeth upward; use fine layer height for teeth. |
| rotating_cage | `stl/rotating_cage.stl` | `/home/diobrando/cad/tourbillon/tourbillon_v20_step/03_rotating_cage_bearing_journal_shaft_retainer_v20.step` | Print drive gear flat; inspect central journal and orbit shaft supports after print. |
| orbit_pinion | `stl/orbit_pinion.stl` | `/home/diobrando/cad/tourbillon/tourbillon_v20_step/04_orbit_pinion_3mm_bore_backlash_teeth_v20.step` | Print flat on gear face; use fine layer height and deburr tooth edges. |
| hand_crank | `stl/hand_crank.stl` | `/home/diobrando/cad/tourbillon/tourbillon_v20_step/05_hand_crank_3mm_shaft_bore_retained_pinion_v20.step` | Print pinion flat with handle upward if supported, or split support only under handle if needed. |

## Files

- `printed_parts.csv`: printed part source, STL, bounding box, and Onshape element IDs.
- `purchased_parts.csv`: MISUMI-style purchased hardware list.
- `assembly_sequence.csv`: assembly order and validation gate per step.
- `gate_summary.json`: passed gates and known native Gear Relation blocker.

## Onshape Evidence

- Mated assembly: https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/ed96fa6ecf577942b84738b4
- Pose snapshots: https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/9d5a5dcebd96c3492b7d3cd7
- Standard hardware reference: https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/71082fad2ecbb26f6b474b06

# CAD-FG-17: Mechanism DSL expansion — tourbillon support

**Status**: `completed`
**Classification**: `executable_now` (approved DSL extension)
**Requires approval**: ✅ User-approved (tourbillon condition: additional DSL must include all elements necessary to create tourbillon mechanism objects)

## Scope

Expand the approved Mechanism DSL operation set to include all cadquery-backed
operations needed to model a **tourbillon** (トゥールビオン) — the rotating
carriage/watchmaking mechanism that neutralises positional gravity error.

## Deliverables

### Code

| File | Change |
|---|---|
| `src/cad_agent/contracts/phase1/parametric_dsl.schema.json` | `oneOf` expanded with 7 new op sub-schemas (`gear`, `escape_wheel`, `balance_wheel`, `lever`, `cage`, `hairspring`, `jewel`) |
| `src/cad_agent/dsl_compiler.py` | `ALLOWED_DSL_OPERATIONS` extended; `PHASE1_REQUIRED_FIELDS` added per op; `_validate_phase1_feature` refactored to resolve all required fields dynamically |
| `src/cad_agent/platform_poc.py` | `ALLOWED_DSL_OPS`/`ADDITIVE_OPS` extended; `GEAR_GENERATION_FAILED`/`ASSEMBLY_CONSTRAINT_FAILED` constants + wiring; `_feature_bbox`/`_feature_volume` with analytic approximations per op; `_build_cadquery_model` → dispatch table (`_CADQUERY_BUILDERS`); 10 builder functions (`_build_box`, `_build_cylinder`, `_annulus`, `_build_gear`, `_build_escape_wheel`, `_build_balance_wheel`, `_build_lever`, `_build_cage`, `_build_hairspring`, `_build_jewel`) |
| `src/cad_agent/assembly_checks.py` | `check_tourbillon_constraints` — distance-from-cage-center containment validation; `TOURBILLON_CAGE_RADIUS_VIOLATION` (= `ASSEMBLY_CONSTRAINT_FAILED`) + `TOURBILLON_NO_CAGE` codes |

### New operations

| Operation | Required fields | Purpose |
|---|---|---|
| `gear` | `module_mm`, `teeth`, `thickness_mm`, `bore_diameter_mm` | Toothed wheel (involute-style polyline approximation) |
| `escape_wheel` | `teeth`, `tip_radius_mm`, `thickness_mm`, `bore_diameter_mm` | Escapement star wheel; optional `tooth_type` (`pointed`|`club`) |
| `balance_wheel` | `outer_diameter_mm`, `rim_width_mm`, `spokes`, `thickness_mm`, `bore_diameter_mm` | Oscillating wheel with rim + spokes |
| `lever` | `length_mm`, `width_mm`, `thickness_mm`, `fork_width_mm`, `pivot_diameter_mm` | Pallet fork with pivot bore |
| `cage` | `outer_diameter_mm`, `arm_count`, `thickness_mm`, `bore_diameter_mm` | Rotating carriage; optional `bridge` (bool, default `true`) |
| `hairspring` | `outer_diameter_mm`, `coils`, `wire_diameter_mm`, `thickness_mm` | Archimedean spiral band |
| `jewel` | `diameter_mm`, `thickness_mm` | Bearing jewel / pivot stone |

All are z-axis extrusions and honour the existing contract (`units = mm`, `$param` references, `axis = "z"`, `positions_mm`).

### Reserved error codes (now active)

| Code | Activated in | Meaning |
|---|---|---|
| `GEAR_GENERATION_FAILED` | `_build_cadquery_model` → `run_cad_runtime` | Additive feature geometry build failed (module/teeth zero, etc.) |
| `ASSEMBLY_CONSTRAINT_FAILED` | `check_tourbillon_constraints` | Tourbillon cage does not contain carried wheels |

### Example

`examples/tourbillon/` — 7 dsl files, requirement + specification, `run_test.py` (assembly pipeline + viewer + tourbillon constraint gating), `README.md`.

### Tests

`tests/test_tourbillon.py` — 7 tests:
- `test_each_new_op_validates_against_schema` — per-op schema pass
- `test_each_new_op_generates_cad` — per-op runtime pass + bbox + STL
- `test_gear_generation_failed_error_code` — teeth=0 surfaces `GEAR_GENERATION_FAILED`
- `test_tourbillon_pipeline_passes_and_viewer_matches_stl` — full pipeline + viewer fidelity
- `test_tourbillon_cage_containment_passes` — positive constraint
- `test_tourbillon_cage_containment_fails_when_escape_exceeds_cage` — negative (escape wheel far exceeds cage radius)
- `test_tourbillon_constraint_missing_cage` — `TOURBILLON_NO_CAGE` code

### Docs updated

- `docs/MECHANISM_DSL_OPERATIONS.md` — 7 new ops + required fields; removed cages/gears from "not approved"
- `docs/MECHANISM_DSL_V1.md` — updated in-scope, deferred, contract summary, acceptance criteria, open decisions
- `docs/CAD_RUNTIME_CONTRACT.md` — `GEAR_GENERATION_FAILED` + `ASSEMBLY_CONSTRAINT_FAILED` moved from reserved to active
- `docs/cad_agent_implementation_plan.md` §4.1 — CAD-FG-17 row
- `TASKS.md` — CAD-FG-17 entry

## Validation gate

| Command | Result |
|---|---|
| `uv run pytest -q` | 236 passed + 2 subtests |
| `bash ./run_cad_agent.sh validate-docs` | pass |
| `bash ./run_cad_agent.sh status` | aligned |
| `git diff --check` | clean |

## Non-goals

- Motion sweep, dynamic balance, or oscillation simulation
- True involute gear tooth profile (polyline approximation used)
- Production Material/PLM/FEA integration
- Bearing rings, bearing seats, gimbal rings (remain deferred)

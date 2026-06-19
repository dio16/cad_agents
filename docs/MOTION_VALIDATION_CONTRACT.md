# Motion Validation Contract

## Status
CAD-P08 Task 08.2 contract. Bounded motion-state schema, deterministic clearance validation, and report shape.

## Purpose
Define the input and output contract for bounded motion validation of approved mechanism fixtures. The validator reports pass/fail and reason codes for the motion-state representation and deterministic clearance rule before any later sweep or workflow-gate work is added.

## Source traceability
- `docs/cadagent_plans/CAD-P08/implementation-plan.md:26-50`
- `docs/cad_agent_detailed_design.md:158-163`
- `docs/cad_agent_implementation_plan.md:71-75`
- `docs/VALIDATION_CONTRACT.md:18-20`

## In scope for Task 08.2
- Bounded rotational motion-state input schema.
- Deterministic schema/state validation.
- Deterministic clearance rule when clearance fields are provided.
- Machine-readable reason codes.
- Motion validation report shape suitable for the CAD-P03 workflow gate.
- Traceability from input state, declared parts, and validation report.

## Non-goals
- FEA or safety analysis.
- Production dynamic simulation.
- Rotational sweep collision detection.
- Full motion validation for unapproved mechanism DSL.
- Approval or override authority. A failed motion validation result remains failed until the Orchestrator receives a valid revision.

## Input schema

The validator consumes mechanism motion-state JSON. Current bounded validation supports `motion_type: "rotation"` only.

```json
{
  "traceability_id": "tr_motion_fixture_valid_1",
  "mechanism_id": "mech_fixture_rotation_1",
  "motion_type": "rotation",
  "rotation_axis": "z",
  "angular_range_deg": {
    "start_deg": 0.0,
    "end_deg": 90.0
  },
  "moving_part_ids": ["rotor"],
  "parts": [
    {
      "part_id": "rotor",
      "traceability_id": "tr_part_rotor_fixture_1"
    }
  ]
}
```

### Required fields
| Field | Type | Rule |
|---|---:|---|
| `rotation_axis` | string | Required. Must be one of `x`, `y`, or `z`. |
| `angular_range_deg` | object | Required. Must contain finite numeric `start_deg` and `end_deg`, with `end_deg > start_deg`. |
| `moving_part_ids` | string[] | Required. Non-empty array of non-empty part IDs. |

### Optional fields
| Field | Type | Rule |
|---|---:|---|
| `traceability_id` | string | Input traceability ID. If absent, the report receives a deterministic generated ID. |
| `mechanism_id` | string | Mechanism identifier for report context. |
| `motion_type` | string | Defaults to `rotation`; any other value fails as unsupported for this bounded phase. |
| `parts` | object[] | Declared parts. If provided, every `moving_part_ids` entry must match a `parts[].part_id`. Each part must include `part_id` and `traceability_id`. |
| `clearance_mm` | number | Optional but coupled with `min_clearance_mm`. If present, must be a finite non-negative number and must be present with `min_clearance_mm`. |
| `min_clearance_mm` | number | Optional but coupled with `clearance_mm`. If present, must be a finite non-negative number. If both are present, validation fails when `clearance_mm < min_clearance_mm`. If both are absent, clearance validation is skipped. |

## Output/report shape

The validator returns a deterministic result object and a JSON report.

```json
{
  "traceability_id": "tr_motion_fixture_valid_1",
  "mechanism_id": "mech_fixture_rotation_1",
  "analysis_scope": "bounded_motion_state_schema_v0",
  "valid": true,
  "status": "pass",
  "overall": "pass",
  "reason_codes": [],
  "failure_locations": [],
  "checks": [],
  "revision_feedback": []
}
```

Failure report shape:

```json
{
  "traceability_id": "tr_motion_<stable-digest>",
  "mechanism_id": null,
  "analysis_scope": "bounded_motion_state_schema_v0",
  "valid": false,
  "status": "fail",
  "overall": "fail",
  "reason_codes": ["MISSING_ROTATION_AXIS"],
  "failure_locations": ["$.rotation_axis"],
  "checks": [
    {
      "name": "rotation_axis_check",
      "status": "fail",
      "reason_code": "MISSING_ROTATION_AXIS"
    }
  ],
  "revision_feedback": [
    {
      "reason_code": "MISSING_ROTATION_AXIS",
      "message": "Add rotation_axis as one of x, y, z."
    }
  ]
}
```

## Reason codes

| Code | Meaning | Revision feedback |
|---|---|---|
| `INVALID_MOTION_STATE` | Input is not a JSON object. | Provide motion-state JSON as an object. |
| `UNSUPPORTED_MOTION_TYPE` | `motion_type` is not `rotation`. | Use `motion_type: "rotation"` for the bounded validator. |
| `MISSING_ROTATION_AXIS` | `rotation_axis` is absent. | Add `rotation_axis` as one of `x`, `y`, or `z`. |
| `INVALID_ROTATION_AXIS` | `rotation_axis` is unsupported. | Use `x`, `y`, or `z`. |
| `MISSING_ANGULAR_RANGE` | `angular_range_deg` is absent. | Add numeric `start_deg` and `end_deg`. |
| `INVALID_ANGULAR_RANGE` | Angular range is malformed or decreasing. | Ensure finite numbers and `end_deg > start_deg`. |
| `MISSING_MOVING_PART_IDS` | `moving_part_ids` is absent or empty. | Add a non-empty list of moving part IDs. |
| `INVALID_MOVING_PART_IDS` | `moving_part_ids` contains invalid entries. | Use a non-empty array of non-empty strings. |
| `MOVING_PART_ID_NOT_FOUND` | A moving part ID is not declared in `parts`. | Declare the moving part in `parts[].part_id`. |
| `MISSING_PART_ID` | A declared part lacks `part_id`. | Add a non-empty `part_id`. |
| `MISSING_PART_TRACEABILITY` | A declared part lacks `traceability_id`. | Add a non-empty `traceability_id`. |
| `INVALID_PARTS` | `parts` is malformed. | Provide `parts` as an array of part objects. |
| `MISSING_CLEARANCE` | `min_clearance_mm` is present but `clearance_mm` is absent. | Add `clearance_mm` when `min_clearance_mm` is provided. |
| `MISSING_MIN_CLEARANCE` | `clearance_mm` is present but `min_clearance_mm` is absent. | Add `min_clearance_mm` when `clearance_mm` is provided. |
| `INVALID_CLEARANCE` | `clearance_mm` is not a finite non-negative number. | Provide a finite non-negative `clearance_mm`. |
| `INVALID_MIN_CLEARANCE` | `min_clearance_mm` is not a finite non-negative number. | Provide a finite non-negative `min_clearance_mm`. |
| `INSUFFICIENT_CLEARANCE` | `clearance_mm` is below `min_clearance_mm`. | Increase `clearance_mm` so it is greater than or equal to `min_clearance_mm`. |

## Workflow gate behavior
- Motion validation is a quality gate, not an approval authority.
- A failure must be passed to the Orchestrator as a validation failure.
- The Orchestrator must keep the workflow in a failed or revision-requested state and must not request export while motion validation is failed.
- Validation failures are not rewritten as pass.
- The deterministic clearance check is executed when either clearance field is present.
- Sweep checks are not executed by Task 08.2 and must not be treated as passed.

## Traceability
- The report always includes `traceability_id`.
- If the input supplies `traceability_id`, the report preserves it.
- If the input omits `traceability_id`, the validator generates a deterministic report traceability ID from the input payload.
- Declared parts must include `traceability_id` so later clearance, sweep, and artifact checks can link moving geometry to source parts.
- Failure locations use JSON-pointer-style paths such as `$.rotation_axis` and `$.parts[0].traceability_id`.

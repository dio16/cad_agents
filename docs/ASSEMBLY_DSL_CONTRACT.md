# Assembly DSL Contract

## Scope

This contract defines the bounded Assembly DSL and deterministic validation scope for simple part placement.

- Simple part placement using axis-aligned bounding boxes.
- Deterministic interference, separation, and adjacency checks.
- Machine-readable reason codes and failure locations for local validation reports.
- Local PoC/Pilot integration through the CAD-P03 workflow gate.

## Non-goals

The following remain explicitly deferred unless separately approved:

- Full B-Rep interference validation.
- Motion validation or mechanism operation validation.
- FEA or dynamic simulation.
- Production assembly storage, PLM, ERP, or MES integration.
- Treating AABB checks as complete geometric assembly validation.

## Part record

Each assembly part record must include:

```json
{
  "part_id": "string",
  "traceability_id": "string",
  "bbox": {
    "min": [0, 0, 0],
    "max": [10, 10, 10]
  }
}
```

The runtime representation maps this to `AssemblyPart(part_id, traceability_id, BBox(...))`.

## Validation checks

### Interference

Two parts interfere when their AABBs overlap on all three axes.

- Reason code: `AABB_INTERFERENCE`
- Failure location: pair of `part_id` values.
- Report includes overlap distance per axis.

### Separation

Two parts are separated when at least one axis has a positive gap.

- Reason code: `AABB_SEPARATION`
- Report includes nearest gap axis and distance.
- Separation is informational unless a minimum separation requirement is violated by a later rule.

### Adjacency

Two parts are adjacent when they touch on one axis and overlap or touch on the other axes, or when the nearest gap is within `tolerance_mm`.

- Reason code: `AABB_ADJACENT`
- Report includes tolerance and gap axis.

## Report shape

A local assembly validation report must include:

```json
{
  "passed": false,
  "analysis_scope": "axis_aligned_bounding_box_only",
  "reason_codes": ["AABB_INTERFERENCE"],
  "failure_locations": [["part_a", "part_b"]],
  "interferences": [],
  "separations": [],
  "adjacent_within_tolerance": [],
  "issues": []
}
```

## Workflow gate rule

Assembly validation failures block export through the CAD-P03 workflow gate by converting the assembly report into `Workflow.handle_validation(...)`. A failing assembly report must keep the workflow in `validation_failed` or `revision_requested` until an approved revision or explicit human escalation occurs.

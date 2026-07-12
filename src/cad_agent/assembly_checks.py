from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class BBox:
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    def as_tuple(self) -> tuple[float, float, float, float, float, float]:
        return (self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z)

    def as_dict(self) -> dict[str, float]:
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "min_z": self.min_z,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "max_z": self.max_z,
        }


@dataclass(frozen=True, slots=True)
class AssemblyPart:
    part_id: str
    traceability_id: str
    bbox: BBox


@dataclass(frozen=True, slots=True)
class AssemblyValidationIssue:
    code: str
    message: str
    part_id: str | None = None


class AssemblyValidationError(ValueError):
    def __init__(self, issues: list[AssemblyValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(issue.message for issue in issues))


@dataclass(frozen=True, slots=True)
class Interference:
    part_a: str
    part_b: str
    overlap_mm: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {"part_a": self.part_a, "part_b": self.part_b, "overlap_mm": dict(self.overlap_mm)}


@dataclass(frozen=True, slots=True)
class Separation:
    part_a: str
    part_b: str
    distance_mm: float
    gap_axis: str

    def as_dict(self) -> dict[str, object]:
        return {"part_a": self.part_a, "part_b": self.part_b, "distance_mm": self.distance_mm, "gap_axis": self.gap_axis}


@dataclass(frozen=True, slots=True)
class Adjacency:
    part_a: str
    part_b: str
    tolerance_mm: float
    gap_axis: str
    gap_mm: float

    def as_dict(self) -> dict[str, object]:
        return {
            "part_a": self.part_a,
            "part_b": self.part_b,
            "tolerance_mm": self.tolerance_mm,
            "gap_axis": self.gap_axis,
            "gap_mm": self.gap_mm,
        }


@dataclass(frozen=True, slots=True)
class AssemblyCheckReport:
    status: str
    analysis_scope: str
    interferences: tuple[Interference, ...]
    separations: tuple[Separation, ...]
    adjacent_within_tolerance: tuple[Adjacency, ...]
    issues: tuple[AssemblyValidationIssue, ...]

    def as_dict(self) -> dict[str, object]:
        reason_codes: list[str] = []
        failure_locations: list[str] = []
        for interference in self.interferences:
            reason_codes.append(AABB_INTERFERENCE)
            failure_locations.append(f"{interference.part_a}:{interference.part_b}")
        for issue in self.issues:
            reason_codes.append(issue.code)
            if issue.part_id is not None:
                failure_locations.append(issue.part_id)
        return {
            "status": self.status,
            "analysis_scope": self.analysis_scope,
            "reason_codes": reason_codes,
            "failure_locations": failure_locations,
            "interferences": [item.as_dict() for item in self.interferences],
            "separations": [item.as_dict() for item in self.separations],
            "adjacent_within_tolerance": [item.as_dict() for item in self.adjacent_within_tolerance],
            "issues": [
                {"code": issue.code, "message": issue.message, "part_id": issue.part_id}
                for issue in self.issues
            ],
        }


AXIS_SPECS = (
    ("x", "min_x", "max_x"),
    ("y", "min_y", "max_y"),
    ("z", "min_z", "max_z"),
)
AABB_INTERFERENCE = "AABB_INTERFERENCE"
AABB_SEPARATION = "AABB_SEPARATION"
AABB_ADJACENT = "AABB_ADJACENT"


def validate_parts(parts: list[AssemblyPart] | tuple[AssemblyPart, ...]) -> list[AssemblyValidationIssue]:
    issues: list[AssemblyValidationIssue] = []
    for index, part in enumerate(parts):
        prefix = f"part[{index}]"
        if not part.part_id:
            issues.append(AssemblyValidationIssue("missing_part_id", f"{prefix}.part_id is required"))
        if not part.traceability_id:
            issues.append(AssemblyValidationIssue("missing_traceability_id", f"{prefix}.traceability_id is required"))
        for axis, min_key, max_key in AXIS_SPECS:
            min_value = getattr(part.bbox, min_key)
            max_value = getattr(part.bbox, max_key)
            if max_value <= min_value:
                issues.append(
                    AssemblyValidationIssue(
                        "invalid_bbox",
                        f"invalid_bbox: {prefix}.bbox {axis} range must have max > min",
                        part.part_id,
                    )
                )
    return issues


def check_interference(
    parts: list[AssemblyPart] | tuple[AssemblyPart, ...],
    tolerance_mm: float = 0.0,
) -> AssemblyCheckReport:
    issues = validate_parts(parts)
    if issues:
        raise AssemblyValidationError(issues)
    if tolerance_mm < 0:
        raise AssemblyValidationError([AssemblyValidationIssue("invalid_tolerance", "invalid_tolerance: tolerance_mm must be non-negative")])

    interferences: list[Interference] = []
    separations: list[Separation] = []
    adjacent: list[Adjacency] = []
    seen_pairs: set[tuple[str, str]] = set()

    for left_index, left in enumerate(parts):
        for right in parts[left_index + 1 :]:
            pair_key = (left.part_id, right.part_id) if left.part_id < right.part_id else (right.part_id, left.part_id)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            overlap: dict[str, float] = {}
            raw_gaps: dict[str, float] = {}
            separation_axes: list[tuple[str, float]] = []
            touch_axes: list[tuple[str, float]] = []
            overlap_axes: list[str] = []
            for axis, left_min_key, left_max_key in AXIS_SPECS:
                right_min_key = left_min_key
                right_max_key = left_max_key
                left_min = getattr(left.bbox, left_min_key)
                left_max = getattr(left.bbox, left_max_key)
                right_min = getattr(right.bbox, right_min_key)
                right_max = getattr(right.bbox, right_max_key)
                raw_gap = max(left_min - right_max, right_min - left_max)
                raw_gaps[axis] = raw_gap
                if raw_gap > 0:
                    separation_axes.append((axis, raw_gap))
                elif raw_gap == 0:
                    touch_axes.append((axis, raw_gap))
                else:
                    overlap_axes.append(axis)
                overlap[axis] = max(0.0, min(left_max, right_max) - max(left_min, right_min))

            if not separation_axes and not touch_axes:
                interferences.append(Interference(left.part_id, right.part_id, overlap))
            elif len(separation_axes) == 1 and separation_axes[0][1] <= tolerance_mm:
                axis, distance = separation_axes[0]
                adjacent.append(Adjacency(left.part_id, right.part_id, tolerance_mm, axis, distance))
            elif separation_axes:
                axis, distance = min(separation_axes, key=lambda item: item[1])
                separations.append(Separation(left.part_id, right.part_id, distance, axis))
            else:
                axis, gap = touch_axes[0]
                adjacent.append(Adjacency(left.part_id, right.part_id, tolerance_mm, axis, gap))

    status = "fail" if interferences else "pass"
    return AssemblyCheckReport(
        status=status,
        analysis_scope="axis_aligned_bounding_box_only",
        interferences=tuple(interferences),
        separations=tuple(separations),
        adjacent_within_tolerance=tuple(adjacent),
        issues=(),
    )


def check_adjacency(
    parts: list[AssemblyPart] | tuple[AssemblyPart, ...],
    tolerance_mm: float = 0.0,
) -> AssemblyCheckReport:
    return check_interference(parts, tolerance_mm=tolerance_mm)


TOURBILLON_CAGE_RADIUS_VIOLATION = "ASSEMBLY_CONSTRAINT_FAILED"
TOURBILLON_NO_CAGE = "TOURBILLON_NO_CAGE"


def check_tourbillon_constraints(
    parts: list[AssemblyPart] | tuple[AssemblyPart, ...],
    tolerance_mm: float = 0.0,
) -> AssemblyCheckReport:
    """Validate that a tourbillon rotating cage physically contains its escapement.

    The cage (a part whose id contains "cage") must have an outer radius that fully
    encloses every carried escapement wheel (ids containing "escape" or "balance").
    Each carried wheel's farthest corner is measured from the cage center; if it
    exceeds the cage outer radius the check fails with ASSEMBLY_CONSTRAINT_FAILED so
    the CAD runtime can surface the reserved contract error code.
    """
    issues = list(validate_parts(parts))
    if tolerance_mm < 0:
        issues.append(AssemblyValidationIssue("invalid_tolerance", "tolerance_mm must be non-negative", None))
    cage = next((p for p in parts if "cage" in p.part_id.lower()), None)
    carried = [p for p in parts if p is not cage and ("escape" in p.part_id.lower() or "balance" in p.part_id.lower())]
    if cage is None:
        issues.append(AssemblyValidationIssue(TOURBILLON_NO_CAGE, "tourbillon assembly is missing a rotating cage part", None))
    else:
        cx = (cage.bbox.min_x + cage.bbox.max_x) / 2.0
        cy = (cage.bbox.min_y + cage.bbox.max_y) / 2.0
        cage_r = max(cage.bbox.max_x - cage.bbox.min_x, cage.bbox.max_y - cage.bbox.min_y) / 2.0
        for p in carried:
            corners = (
                (p.bbox.min_x, p.bbox.min_y),
                (p.bbox.max_x, p.bbox.min_y),
                (p.bbox.min_x, p.bbox.max_y),
                (p.bbox.max_x, p.bbox.max_y),
            )
            dist = max(math.hypot(x - cx, y - cy) for x, y in corners)
            if dist > cage_r + tolerance_mm:
                issues.append(
                    AssemblyValidationIssue(
                        TOURBILLON_CAGE_RADIUS_VIOLATION,
                        f"{p.part_id} reaches {dist:.3f}mm from cage center, exceeds cage radius {cage_r:.3f}mm",
                        p.part_id,
                    )
                )
    status = "fail" if issues else "pass"
    return AssemblyCheckReport(
        status=status,
        analysis_scope="tourbillon_cage_containment",
        interferences=(),
        separations=(),
        adjacent_within_tolerance=(),
        issues=tuple(issues),
    )


@dataclass(frozen=True, slots=True)
class GearSpec:
    """Minimal gear specification for mesh validation."""
    module_mm: float
    teeth: int


GEAR_MESH_DISTANCE = "GEAR_MESH_DISTANCE"
GEAR_MESH_MODULE_MISMATCH = "GEAR_MESH_MODULE_MISMATCH"
GEAR_MESH_MISSING_SPEC = "GEAR_MESH_MISSING_SPEC"


def check_gear_mesh(
    parts: list[AssemblyPart] | tuple[AssemblyPart, ...],
    gear_specs: dict[str, GearSpec],
    meshing_pairs: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    tolerance_mm: float = 0.5,
) -> AssemblyCheckReport:
    """Validate that paired gears are positioned at the correct centre distance.

    For each (part_a, part_b) pair the *required* centre distance is computed
    from :math:`m \\cdot (z_a + z_b) / 2` and compared to the actual Euclidean
    distance between the parts' bounding-box centres.  Modules must match.
    """
    issues = list(validate_parts(parts))
    for part_a, part_b in meshing_pairs:
        a = next((p for p in parts if p.part_id == part_a), None)
        b = next((p for p in parts if p.part_id == part_b), None)
        if a is None or b is None:
            missing = part_a if a is None else part_b
            issues.append(AssemblyValidationIssue("GEAR_MESH_MISSING_PART", f"part '{missing}' not found"))
            continue
        sa = gear_specs.get(part_a)
        sb = gear_specs.get(part_b)
        if sa is None or sb is None:
            missing = part_a if sa is None else part_b
            issues.append(AssemblyValidationIssue(GEAR_MESH_MISSING_SPEC, f"gear spec missing for '{missing}'"))
            continue
        if abs(sa.module_mm - sb.module_mm) > 1e-9:
            issues.append(
                AssemblyValidationIssue(GEAR_MESH_MODULE_MISMATCH,
                    f"{part_a} (m={sa.module_mm}) != {part_b} (m={sb.module_mm})"))
            continue
        required_cd = sa.module_mm * (sa.teeth + sb.teeth) / 2.0
        ax = (a.bbox.min_x + a.bbox.max_x) / 2.0
        ay = (a.bbox.min_y + a.bbox.max_y) / 2.0
        bx = (b.bbox.min_x + b.bbox.max_x) / 2.0
        by = (b.bbox.min_y + b.bbox.max_y) / 2.0
        actual_cd = math.hypot(ax - bx, ay - by)
        error = abs(actual_cd - required_cd)
        if error > tolerance_mm:
            issues.append(
                AssemblyValidationIssue(GEAR_MESH_DISTANCE,
                    f"{part_a}-{part_b}: required centre distance {required_cd:.3f} mm, "
                    f"actual {actual_cd:.3f} mm (error {error:.3f} mm > {tolerance_mm} mm)"))
    status = "fail" if issues else "pass"
    return AssemblyCheckReport(
        status=status,
        analysis_scope="gear_mesh_centre_distance",
        interferences=(),
        separations=(),
        adjacent_within_tolerance=(),
        issues=tuple(issues),
    )




SHAFT_BORE_VIOLATION = "SHAFT_BORE_VIOLATION"
SHAFT_BORE_MISALIGNED = "SHAFT_BORE_MISALIGNED"


def check_shaft_clearance(
    bearing_part: AssemblyPart,
    shaft_part: AssemblyPart,
    bore_diameter_mm: float,
    shaft_diameter_mm: float,
    clearance_min_mm: float = 0.2,
    coaxial_tolerance_mm: float = 1.0,
) -> AssemblyCheckReport:
    """Validate that a shaft fits through a bearing bore with adequate clearance.

    Checks that *bearing_part* and *shaft_part* are coaxial (their bounding-box
    centres lie within *coaxial_tolerance_mm* in the x‑y plane) and that the
    bore diameter exceeds the shaft diameter by at least *clearance_min_mm*.
    """
    issues = list(validate_parts([bearing_part, shaft_part]))
    if not issues:
        bx = (bearing_part.bbox.min_x + bearing_part.bbox.max_x) / 2.0
        by = (bearing_part.bbox.min_y + bearing_part.bbox.max_y) / 2.0
        sx = (shaft_part.bbox.min_x + shaft_part.bbox.max_x) / 2.0
        sy = (shaft_part.bbox.min_y + shaft_part.bbox.max_y) / 2.0
        dx = abs(bx - sx)
        dy = abs(by - sy)
        if dx > coaxial_tolerance_mm or dy > coaxial_tolerance_mm:
            issues.append(
                AssemblyValidationIssue(SHAFT_BORE_MISALIGNED,
                    f"bearing centre ({bx:.1f},{by:.1f}) vs shaft centre ({sx:.1f},{sy:.1f}) "
                    f"— offset ({dx:.3f},{dy:.3f}) > {coaxial_tolerance_mm} mm"))
        if bore_diameter_mm < shaft_diameter_mm + clearance_min_mm:
            issues.append(
                AssemblyValidationIssue(SHAFT_BORE_VIOLATION,
                    f"bore ⌀{bore_diameter_mm:.2f} mm < shaft ⌀{shaft_diameter_mm:.2f} mm "
                    f"+ clearance {clearance_min_mm:.2f} mm"))
    status = "fail" if issues else "pass"
    return AssemblyCheckReport(
        status=status,
        analysis_scope="shaft_clearance",
        interferences=(),
        separations=(),
        adjacent_within_tolerance=(),
        issues=tuple(issues),
    )


TOURBILLON_MECHANICS_VIOLATION = "TOURBILLON_MECHANICS_VIOLATION"


def check_tourbillon_mechanics(
    parts: list[AssemblyPart] | tuple[AssemblyPart, ...],
    *,
    fixed_wheel_id: str = "fixed_wheel",
    cage_id: str = "cage",
    cage_bore_mm: float,
    shaft_diameter_mm: float,
    meshing_pairs: list[tuple[str, str]] | None = None,
    gear_specs: dict[str, GearSpec] | None = None,
    gear_mesh_tolerance_mm: float = 0.5,
) -> AssemblyCheckReport:
    """Composite tourbillon mechanical validation.

    Runs every mechanically meaningful check for a tourbillon assembly:

    1. Cage bore accommodates the central pivot shaft (``check_shaft_clearance``).
    2. Cage physically contains the carried escapement wheels
       (``check_tourbillon_constraints``).
    3. Every declared meshing pair is at the correct centre distance
       (``check_gear_mesh``).

    Returns a single report aggregating all issues.
    """
    all_issues: list[AssemblyValidationIssue] = []

    # 1. Shaft clearance: cage bore vs central pivot shaft
    cage = next((p for p in parts if p.part_id == cage_id), None)
    fixed = next((p for p in parts if p.part_id == fixed_wheel_id), None)
    if cage is not None and fixed is not None:
        sc = check_shaft_clearance(
            cage, fixed,
            bore_diameter_mm=cage_bore_mm,
            shaft_diameter_mm=shaft_diameter_mm,
            clearance_min_mm=0.5,
        )
        all_issues.extend(sc.issues)
    else:
        missing = cage_id if cage is None else fixed_wheel_id
        all_issues.append(AssemblyValidationIssue(TOURBILLON_MECHANICS_VIOLATION,
            f"tourbillon mechanics: missing part '{missing}'"))

    # 2. Cage containment
    tc = check_tourbillon_constraints(parts)
    all_issues.extend(tc.issues)

    # 3. Gear mesh for declared pairs
    if meshing_pairs and gear_specs:
        gm = check_gear_mesh(parts, gear_specs, meshing_pairs, tolerance_mm=gear_mesh_tolerance_mm)
        all_issues.extend(gm.issues)

    status = "fail" if all_issues else "pass"
    return AssemblyCheckReport(
        status=status,
        analysis_scope="tourbillon_mechanics",
        interferences=(),
        separations=(),
        adjacent_within_tolerance=(),
        issues=tuple(all_issues),
    )

def assembly_report_to_validation_result(report: AssemblyCheckReport | dict[str, object]) -> dict[str, object]:
    if isinstance(report, dict):
        reason_codes = report.get("reason_codes")
        failure_locations = report.get("failure_locations")
        return {
            "passed": bool(report.get("passed", not reason_codes)),
            "reason_codes": [str(code) for code in reason_codes] if isinstance(reason_codes, list) else [],
            "failure_locations": [str(location) for location in failure_locations] if isinstance(failure_locations, list) else [],
            "analysis_scope": report.get("analysis_scope", "assembly_validation"),
            "report": report,
        }

    reason_codes: list[str] = []
    failure_locations: list[str] = []

    for interference in report.interferences:
        reason_codes.append(AABB_INTERFERENCE)
        failure_locations.append(f"{interference.part_a}:{interference.part_b}")

    for issue in report.issues:
        reason_codes.append(issue.code)
        if issue.part_id is not None:
            failure_locations.append(issue.part_id)

    return {
        "passed": not reason_codes,
        "reason_codes": reason_codes,
        "failure_locations": failure_locations,
        "analysis_scope": report.analysis_scope,
        "report": report.as_dict(),
    }

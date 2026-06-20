from __future__ import annotations

from dataclasses import dataclass


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

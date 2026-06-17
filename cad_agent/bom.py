from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping

from cad_agent.material_catalog import KNOWN_MANUFACTURING_PROFILES, KNOWN_MATERIAL_IDS, get_material


@dataclass(frozen=True, slots=True)
class BOMPart:
    part_id: str
    traceability_id: str
    quantity: float
    material: str
    manufacturing_profile: str
    volume_mm3: float | None = None
    bbox_mm: Mapping[str, float] | None = None
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BOMValidationIssue:
    code: str
    message: str
    part_id: str | None = None


class BOMValidationError(ValueError):
    def __init__(self, issues: list[BOMValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(issue.message for issue in issues))


@dataclass(frozen=True, slots=True)
class BOMItem:
    part_id: str
    traceability_id: str
    quantity: float
    material: str
    manufacturing_profile: str
    volume_mm3: float | None
    weight_g: float | None
    cost: dict[str, Any]
    traceability_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "part_id": self.part_id,
            "traceability_id": self.traceability_id,
            "quantity": self.quantity,
            "material": self.material,
            "manufacturing_profile": self.manufacturing_profile,
            "volume_mm3": self.volume_mm3,
            "weight_g": self.weight_g,
            "cost": dict(self.cost),
            "traceability_ids": list(self.traceability_ids),
        }


@dataclass(frozen=True, slots=True)
class BOM:
    bom_id: str
    items: tuple[BOMItem, ...]
    total_weight_g: float | None
    total_cost: dict[str, Any]
    validation_status: str
    issues: tuple[BOMValidationIssue, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "bom_id": self.bom_id,
            "items": [item.as_dict() for item in self.items],
            "total_weight_g": self.total_weight_g,
            "total_cost": dict(self.total_cost),
            "validation_status": self.validation_status,
            "issues": [
                {"code": issue.code, "message": issue.message, "part_id": issue.part_id}
                for issue in self.issues
            ],
        }


def validate_parts(parts: list[BOMPart] | tuple[BOMPart, ...]) -> list[BOMValidationIssue]:
    issues: list[BOMValidationIssue] = []
    for index, part in enumerate(parts):
        prefix = f"part[{index}]"
        if not part.part_id:
            issues.append(BOMValidationIssue("missing_part_id", f"{prefix}.part_id is required"))
        if not part.traceability_id:
            issues.append(BOMValidationIssue("missing_traceability_id", f"{prefix}.traceability_id is required"))
        if part.quantity <= 0:
            issues.append(
                BOMValidationIssue(
                    "invalid_quantity",
                    f"invalid_quantity: {prefix}.quantity must be positive",
                    part.part_id or None,
                )
            )
        if part.material not in KNOWN_MATERIAL_IDS:
            issues.append(
                BOMValidationIssue(
                    "unknown_material",
                    f"unknown_material: {prefix}.material is not in skeleton catalog: {part.material}",
                    part.part_id or None,
                )
            )
        if part.manufacturing_profile not in KNOWN_MANUFACTURING_PROFILES:
            issues.append(
                BOMValidationIssue(
                    "unknown_manufacturing_profile",
                    f"unknown_manufacturing_profile: {prefix}.manufacturing_profile is not supported: {part.manufacturing_profile}",
                    part.part_id or None,
                )
            )
        if part.volume_mm3 is not None and part.volume_mm3 <= 0:
            issues.append(
                BOMValidationIssue(
                    "invalid_volume",
                    f"invalid_volume: {prefix}.volume_mm3 must be positive",
                    part.part_id or None,
                )
            )
        if part.bbox_mm is not None:
            bbox_issue = _validate_bbox_mapping(part.bbox_mm, part.part_id)
            if bbox_issue is not None:
                issues.append(bbox_issue)
    return issues


def build_bom(parts: list[BOMPart] | tuple[BOMPart, ...], bom_id: str = "bom_v2_skeleton") -> BOM:
    issues = validate_parts(parts)
    if issues:
        raise BOMValidationError(issues)

    grouped: dict[tuple[str, str, str], list[BOMPart]] = defaultdict(list)
    for part in parts:
        grouped[(part.part_id, part.material, part.manufacturing_profile)].append(part)

    items: list[BOMItem] = []
    for key in sorted(grouped):
        part_id, material, profile = key
        group = grouped[key]
        quantity = sum(part.quantity for part in group)
        volume_values: list[float] = []
        for part in group:
            volume = _volume_mm3(part)
            if volume is not None:
                volume_values.append(volume * part.quantity)
        has_geometry = any(value is not None for value in volume_values)
        volume = sum(value for value in volume_values if value is not None)
        density = get_material(material).density_g_cm3
        weight = round(volume * density / 1000.0, 6) if has_geometry else None
        items.append(
            BOMItem(
                part_id=part_id,
                traceability_id=group[0].traceability_id,
                quantity=quantity,
                material=material,
                manufacturing_profile=profile,
                volume_mm3=round(volume, 6) if has_geometry else None,
                weight_g=weight,
                cost=stub_cost(),
                traceability_ids=tuple(sorted(part.traceability_id for part in group)),
            )
        )

    total_weight = round(sum(item.weight_g or 0.0 for item in items), 6) if any(item.weight_g is not None for item in items) else None
    return BOM(
        bom_id=bom_id,
        items=tuple(items),
        total_weight_g=total_weight,
        total_cost=stub_cost(),
        validation_status="pass",
        issues=(),
    )


def stub_cost() -> dict[str, Any]:
    return {"status": "stub", "currency": "JPY", "amount": None}


def _volume_mm3(part: BOMPart) -> float | None:
    if part.volume_mm3 is not None:
        return part.volume_mm3
    if part.bbox_mm is None:
        return None
    length = part.bbox_mm.get("length")
    width = part.bbox_mm.get("width")
    height = part.bbox_mm.get("height")
    if length is None or width is None or height is None:
        return None
    return float(length * width * height)


def _validate_bbox_mapping(bbox: Mapping[str, float], part_id: str | None) -> BOMValidationIssue | None:
    required = ("length", "width", "height")
    missing = [key for key in required if key not in bbox]
    if missing:
        return BOMValidationIssue("invalid_bbox", f"bbox_mm missing required keys: {', '.join(missing)}", part_id)
    invalid = [key for key in required if bbox[key] <= 0]
    if invalid:
        return BOMValidationIssue("invalid_bbox", f"invalid_bbox: bbox_mm keys must be positive: {', '.join(invalid)}", part_id)
    return None

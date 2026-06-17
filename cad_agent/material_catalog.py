from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


UNITS = {
    "density": "g/cm3",
    "strength": "MPa",
    "elastic_modulus": "MPa",
    "temperature": "degC",
    "thermal_conductivity": "W/(m*K)",
}

CATALOG_ID = "cad_agent_material_catalog_v2_skeleton"
DATA_STATUS = "skeleton_stub"
REFERENCE_ONLY = True
REFERENCE_NOTE = (
    "Values are approximate placeholders for Production v2 data-model stubs. "
    "They are not production design allowables and must be replaced by qualified material data."
)


@dataclass(frozen=True, slots=True)
class MechanicalProperties:
    tensile_strength_mpa: float | None
    yield_strength_mpa: float | None
    elastic_modulus_mpa: float | None
    elongation_at_break_percent: float | None


@dataclass(frozen=True, slots=True)
class ThermalProperties:
    melting_point_c: float | None
    glass_transition_c: float | None
    max_service_temperature_c: float | None
    thermal_conductivity_w_m_k: float | None


@dataclass(frozen=True, slots=True)
class Material:
    material_id: str
    name: str
    category: str
    density_g_cm3: float
    mechanical: MechanicalProperties
    thermal: ThermalProperties
    manufacturing_profiles: tuple[str, ...]
    units: Mapping[str, str]
    data_status: str = DATA_STATUS
    reference_only: bool = REFERENCE_ONLY
    notes: str = REFERENCE_NOTE

    def as_dict(self) -> dict[str, object]:
        return {
            "material_id": self.material_id,
            "name": self.name,
            "category": self.category,
            "density_g_cm3": self.density_g_cm3,
            "mechanical": {
                "tensile_strength_mpa": self.mechanical.tensile_strength_mpa,
                "yield_strength_mpa": self.mechanical.yield_strength_mpa,
                "elastic_modulus_mpa": self.mechanical.elastic_modulus_mpa,
                "elongation_at_break_percent": self.mechanical.elongation_at_break_percent,
            },
            "thermal": {
                "melting_point_c": self.thermal.melting_point_c,
                "glass_transition_c": self.thermal.glass_transition_c,
                "max_service_temperature_c": self.thermal.max_service_temperature_c,
                "thermal_conductivity_w_m_k": self.thermal.thermal_conductivity_w_m_k,
            },
            "manufacturing_profiles": list(self.manufacturing_profiles),
            "units": dict(self.units),
            "data_status": self.data_status,
            "reference_only": self.reference_only,
            "notes": self.notes,
        }


PLA = Material(
    material_id="PLA",
    name="Polylactic Acid",
    category="polymer_fdm",
    density_g_cm3=1.24,
    mechanical=MechanicalProperties(
        tensile_strength_mpa=60.0,
        yield_strength_mpa=None,
        elastic_modulus_mpa=3500.0,
        elongation_at_break_percent=4.0,
    ),
    thermal=ThermalProperties(
        melting_point_c=None,
        glass_transition_c=60.0,
        max_service_temperature_c=55.0,
        thermal_conductivity_w_m_k=0.13,
    ),
    manufacturing_profiles=("fdm_standard",),
    units=MappingProxyType(UNITS),
)

PETG = Material(
    material_id="PETG",
    name="Polyethylene Terephthalate Glycol",
    category="polymer_fdm",
    density_g_cm3=1.27,
    mechanical=MechanicalProperties(
        tensile_strength_mpa=50.0,
        yield_strength_mpa=None,
        elastic_modulus_mpa=2100.0,
        elongation_at_break_percent=130.0,
    ),
    thermal=ThermalProperties(
        melting_point_c=None,
        glass_transition_c=80.0,
        max_service_temperature_c=70.0,
        thermal_conductivity_w_m_k=0.20,
    ),
    manufacturing_profiles=("fdm_standard",),
    units=MappingProxyType(UNITS),
)

ABS = Material(
    material_id="ABS",
    name="Acrylonitrile Butadiene Styrene",
    category="polymer_fdm_injection",
    density_g_cm3=1.04,
    mechanical=MechanicalProperties(
        tensile_strength_mpa=40.0,
        yield_strength_mpa=45.0,
        elastic_modulus_mpa=2300.0,
        elongation_at_break_percent=20.0,
    ),
    thermal=ThermalProperties(
        melting_point_c=None,
        glass_transition_c=105.0,
        max_service_temperature_c=85.0,
        thermal_conductivity_w_m_k=0.17,
    ),
    manufacturing_profiles=("fdm_standard", "injection_molding"),
    units=MappingProxyType(UNITS),
)

ALUMINUM_6061_T6 = Material(
    material_id="6061-T6",
    name="6061-T6 Aluminum Alloy",
    category="metal_aluminum",
    density_g_cm3=2.70,
    mechanical=MechanicalProperties(
        tensile_strength_mpa=310.0,
        yield_strength_mpa=276.0,
        elastic_modulus_mpa=68900.0,
        elongation_at_break_percent=12.0,
    ),
    thermal=ThermalProperties(
        melting_point_c=650.0,
        glass_transition_c=None,
        max_service_temperature_c=150.0,
        thermal_conductivity_w_m_k=167.0,
    ),
    manufacturing_profiles=("cnc_machining",),
    units=MappingProxyType(UNITS),
)

POM = Material(
    material_id="POM",
    name="Polyoxymethylene / Acetal",
    category="polymer_engineering",
    density_g_cm3=1.42,
    mechanical=MechanicalProperties(
        tensile_strength_mpa=68.0,
        yield_strength_mpa=65.0,
        elastic_modulus_mpa=2800.0,
        elongation_at_break_percent=30.0,
    ),
    thermal=ThermalProperties(
        melting_point_c=175.0,
        glass_transition_c=None,
        max_service_temperature_c=90.0,
        thermal_conductivity_w_m_k=0.31,
    ),
    manufacturing_profiles=("injection_molding", "cnc_machining"),
    units=MappingProxyType(UNITS),
)

STEEL_17_4PH = Material(
    material_id="17-4PH",
    name="17-4 PH Stainless Steel",
    category="metal_stainless",
    density_g_cm3=7.78,
    mechanical=MechanicalProperties(
        tensile_strength_mpa=930.0,
        yield_strength_mpa=724.0,
        elastic_modulus_mpa=196000.0,
        elongation_at_break_percent=10.0,
    ),
    thermal=ThermalProperties(
        melting_point_c=1440.0,
        glass_transition_c=None,
        max_service_temperature_c=300.0,
        thermal_conductivity_w_m_k=18.0,
    ),
    manufacturing_profiles=("cnc_machining", "metal_laser_powder_bed_fusion"),
    units=MappingProxyType(UNITS),
)


_MATERIALS: dict[str, Material] = {
    PLA.material_id: PLA,
    PETG.material_id: PETG,
    ABS.material_id: ABS,
    ALUMINUM_6061_T6.material_id: ALUMINUM_6061_T6,
    POM.material_id: POM,
    STEEL_17_4PH.material_id: STEEL_17_4PH,
}

MATERIAL_CATALOG: Mapping[str, Material] = MappingProxyType(_MATERIALS)
KNOWN_MATERIAL_IDS = frozenset(MATERIAL_CATALOG)
KNOWN_MANUFACTURING_PROFILES = frozenset(
    profile for material in MATERIAL_CATALOG.values() for profile in material.manufacturing_profiles
)


def list_material_ids() -> tuple[str, ...]:
    return tuple(sorted(MATERIAL_CATALOG))


def get_material(material_id: str) -> Material:
    try:
        return MATERIAL_CATALOG[material_id]
    except KeyError as exc:
        raise KeyError(f"unknown material_id: {material_id}") from exc


def has_material(material_id: str) -> bool:
    return material_id in MATERIAL_CATALOG


def render_catalog() -> dict[str, object]:
    return {
        "catalog_id": CATALOG_ID,
        "data_status": DATA_STATUS,
        "reference_only": REFERENCE_ONLY,
        "units": dict(UNITS),
        "materials": [MATERIAL_CATALOG[material_id].as_dict() for material_id in list_material_ids()],
    }

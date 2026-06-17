from __future__ import annotations

import unittest

from cad_agent.material_catalog import (
    CATALOG_ID,
    DATA_STATUS,
    KNOWN_MATERIAL_IDS,
    MATERIAL_CATALOG,
    REFERENCE_ONLY,
    get_material,
    has_material,
    list_material_ids,
    render_catalog,
)


class MaterialCatalogTest(unittest.TestCase):
    def test_all_required_material_ids_exist(self) -> None:
        self.assertEqual(set(KNOWN_MATERIAL_IDS), {"PLA", "PETG", "ABS", "6061-T6", "POM", "17-4PH"})
        self.assertEqual(list_material_ids(), ("17-4PH", "6061-T6", "ABS", "PETG", "PLA", "POM"))

    def test_lookup_by_material_id(self) -> None:
        material = get_material("6061-T6")

        self.assertEqual(material.material_id, "6061-T6")
        self.assertEqual(material.name, "6061-T6 Aluminum Alloy")
        self.assertEqual(material.density_g_cm3, 2.70)
        self.assertIn("cnc_machining", material.manufacturing_profiles)

    def test_catalog_is_immutable_mapping(self) -> None:
        self.assertTrue(has_material("PLA"))
        with self.assertRaises(TypeError):
            MATERIAL_CATALOG["PLA"] = "mutated"  # type: ignore[index]

    def test_stub_reference_metadata_is_present(self) -> None:
        material = get_material("PLA")

        self.assertEqual(material.data_status, DATA_STATUS)
        self.assertTrue(material.reference_only)
        self.assertIn("not production design allowables", material.notes)
        self.assertEqual(material.units["density"], "g/cm3")
        self.assertEqual(material.units["temperature"], "degC")

    def test_material_units_are_immutable(self) -> None:
        material = get_material("PLA")

        with self.assertRaises(TypeError):
            material.units["density"] = "mutated"  # type: ignore[index]

    def test_unknown_material_lookup_fails(self) -> None:
        with self.assertRaisesRegex(KeyError, "unknown material_id: UNKNOWN"):
            get_material("UNKNOWN")

    def test_render_catalog_shape(self) -> None:
        rendered = render_catalog()

        self.assertEqual(rendered["catalog_id"], CATALOG_ID)
        self.assertEqual(rendered["data_status"], DATA_STATUS)
        self.assertTrue(rendered["reference_only"])
        materials = rendered["materials"]
        self.assertIsInstance(materials, list)
        assert isinstance(materials, list)
        self.assertEqual(len(materials), 6)
        first = materials[0]
        self.assertIsInstance(first, dict)
        assert isinstance(first, dict)
        self.assertEqual(first["material_id"], "17-4PH")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from cad_agent.bom import BOMPart, BOMValidationError, build_bom, stub_cost


class BOMTest(unittest.TestCase):
    def test_quantity_aggregation_by_part_material_profile(self) -> None:
        bom = build_bom(
            [
                BOMPart("bracket", "tr_bracket_a", 2, "PLA", "fdm_standard", volume_mm3=1000),
                BOMPart("bracket", "tr_bracket_b", 3, "PLA", "fdm_standard", volume_mm3=500),
                BOMPart("shaft", "tr_shaft", 1, "6061-T6", "cnc_machining", volume_mm3=2000),
            ]
        )

        self.assertEqual(bom.validation_status, "pass")
        self.assertEqual(len(bom.items), 2)
        self.assertEqual(bom.items[0].part_id, "bracket")
        self.assertEqual(bom.items[0].quantity, 5)
        self.assertEqual(bom.items[0].traceability_ids, ("tr_bracket_a", "tr_bracket_b"))
        self.assertEqual(bom.items[0].volume_mm3, 3500)
        self.assertIsNotNone(bom.items[0].weight_g)
        assert bom.items[0].weight_g is not None
        self.assertAlmostEqual(bom.items[0].weight_g, 4.34)
        self.assertIsNotNone(bom.items[1].weight_g)
        assert bom.items[1].weight_g is not None
        self.assertAlmostEqual(bom.items[1].weight_g, 5.4)
        self.assertIsNotNone(bom.total_weight_g)
        assert bom.total_weight_g is not None
        self.assertAlmostEqual(bom.total_weight_g, 9.74)

    def test_weight_scales_by_quantity(self) -> None:
        bom = build_bom([BOMPart("plate", "tr_plate", 4, "PLA", "fdm_standard", volume_mm3=100)])

        self.assertEqual(bom.items[0].volume_mm3, 400)
        self.assertIsNotNone(bom.items[0].weight_g)
        assert bom.items[0].weight_g is not None
        self.assertAlmostEqual(bom.items[0].weight_g, 0.496)

    def test_bbox_weight_stub_from_volume(self) -> None:
        bom = build_bom(
            [
                BOMPart(
                    "block",
                    "tr_block",
                    1,
                    "PETG",
                    "fdm_standard",
                    bbox_mm={"length": 10, "width": 10, "height": 10},
                )
            ]
        )

        self.assertEqual(bom.items[0].volume_mm3, 1000)
        self.assertIsNotNone(bom.items[0].weight_g)
        assert bom.items[0].weight_g is not None
        self.assertAlmostEqual(bom.items[0].weight_g, 1.27)

    def test_missing_geometry_weight_is_none(self) -> None:
        bom = build_bom([BOMPart("concept", "tr_concept", 1, "PLA", "fdm_standard")])

        self.assertIsNone(bom.items[0].volume_mm3)
        self.assertIsNone(bom.items[0].weight_g)
        self.assertIsNone(bom.total_weight_g)

    def test_cost_is_stub_shaped(self) -> None:
        bom = build_bom([BOMPart("concept", "tr_concept", 1, "PLA", "fdm_standard")])

        self.assertEqual(bom.items[0].cost, stub_cost())
        self.assertEqual(bom.total_cost, stub_cost())

    def test_unknown_material_validation_error(self) -> None:
        with self.assertRaisesRegex(BOMValidationError, "unknown_material"):
            build_bom([BOMPart("bad", "tr_bad", 1, "UNKNOWN", "fdm_standard")])

    def test_unknown_manufacturing_profile_validation_error(self) -> None:
        with self.assertRaisesRegex(BOMValidationError, "unknown_manufacturing_profile"):
            build_bom([BOMPart("bad", "tr_bad", 1, "PLA", "unknown_profile")])

    def test_invalid_quantity_validation_error(self) -> None:
        with self.assertRaisesRegex(BOMValidationError, "invalid_quantity"):
            build_bom([BOMPart("bad", "tr_bad", 0, "PLA", "fdm_standard")])

    def test_invalid_bbox_validation_error(self) -> None:
        with self.assertRaisesRegex(BOMValidationError, "invalid_bbox"):
            build_bom(
                [
                    BOMPart(
                        "bad",
                        "tr_bad",
                        1,
                        "PLA",
                        "fdm_standard",
                        bbox_mm={"length": 10, "width": -1, "height": 10},
                    )
                ]
            )


if __name__ == "__main__":
    unittest.main()

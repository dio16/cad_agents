from __future__ import annotations

import unittest

from cad_agent.assembly_checks import AssemblyPart, AssemblyValidationError, BBox, check_interference


class AssemblyChecksTest(unittest.TestCase):
    def test_aabb_interference_detected(self) -> None:
        report = check_interference(
            [
                AssemblyPart("a", "tr_a", BBox(0, 0, 0, 10, 10, 10)),
                AssemblyPart("b", "tr_b", BBox(5, 5, 5, 15, 15, 15)),
            ]
        )

        self.assertEqual(report.status, "fail")
        self.assertEqual(report.analysis_scope, "axis_aligned_bounding_box_only")
        self.assertEqual(len(report.interferences), 1)
        self.assertEqual(report.interferences[0].part_a, "a")
        self.assertEqual(report.interferences[0].part_b, "b")
        self.assertEqual(report.interferences[0].overlap_mm, {"x": 5, "y": 5, "z": 5})

    def test_separated_bboxes_return_no_interference(self) -> None:
        report = check_interference(
            [
                AssemblyPart("a", "tr_a", BBox(0, 0, 0, 10, 10, 10)),
                AssemblyPart("b", "tr_b", BBox(20, 0, 0, 30, 10, 10)),
            ]
        )

        self.assertEqual(report.status, "pass")
        self.assertEqual(len(report.interferences), 0)
        self.assertEqual(len(report.separations), 1)
        self.assertEqual(report.separations[0].gap_axis, "x")
        self.assertAlmostEqual(report.separations[0].distance_mm, 10)

    def test_adjacent_within_tolerance(self) -> None:
        report = check_interference(
            [
                AssemblyPart("a", "tr_a", BBox(0, 0, 0, 10, 10, 10)),
                AssemblyPart("b", "tr_b", BBox(10.5, 5, 0, 20.5, 15, 10)),
            ],
            tolerance_mm=1.0,
        )

        self.assertEqual(report.status, "pass")
        self.assertEqual(len(report.interferences), 0)
        self.assertEqual(len(report.adjacent_within_tolerance), 1)
        self.assertEqual(report.adjacent_within_tolerance[0].gap_axis, "x")
        self.assertAlmostEqual(report.adjacent_within_tolerance[0].gap_mm, 0.5)

    def test_adjacent_outside_tolerance_is_separation(self) -> None:
        report = check_interference(
            [
                AssemblyPart("a", "tr_a", BBox(0, 0, 0, 10, 10, 10)),
                AssemblyPart("b", "tr_b", BBox(12, 0, 0, 20, 10, 10)),
            ],
            tolerance_mm=1.0,
        )

        self.assertEqual(report.status, "pass")
        self.assertEqual(report.interferences, ())
        self.assertEqual(report.adjacent_within_tolerance, ())
        self.assertEqual(len(report.separations), 1)
        self.assertAlmostEqual(report.separations[0].distance_mm, 2)

    def test_invalid_bbox_validation_error(self) -> None:
        with self.assertRaisesRegex(AssemblyValidationError, "invalid_bbox"):
            check_interference([AssemblyPart("bad", "tr_bad", BBox(0, 0, 0, 0, 10, 10))])

    def test_negative_tolerance_validation_error(self) -> None:
        with self.assertRaisesRegex(AssemblyValidationError, "invalid_tolerance"):
            check_interference([], tolerance_mm=-0.1)

    def test_report_dict_shape(self) -> None:
        report = check_interference(
            [
                AssemblyPart("a", "tr_a", BBox(0, 0, 0, 10, 10, 10)),
                AssemblyPart("b", "tr_b", BBox(20, 0, 0, 30, 10, 10)),
            ]
        )

        rendered = report.as_dict()
        separations = rendered["separations"]
        self.assertIsInstance(separations, list)
        assert isinstance(separations, list)
        first = separations[0]
        self.assertIsInstance(first, dict)
        assert isinstance(first, dict)
        self.assertEqual(first["gap_axis"], "x")


if __name__ == "__main__":
    unittest.main()

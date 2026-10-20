"""Counterexamples where hidden constructor choices erased observable evidence."""
import hashlib
import json
import unittest

from arc_agi2.augmentation import transformed
from tasks import task_2dd70a9a, task_342dd610


class VisibleEvidenceTests(unittest.TestCase):
    def test_overwritten_source_dot_cannot_leave_a_second_output(self):
        pair = task_342dd610.generate(
            size=10, rows=[4, 4], cols=[4, 4], colors=[1, 2])
        self.assertIsNone(pair["input"])
        self.assertIsNone(pair["output"])

    def test_separate_dots_keep_distinct_motion_targets(self):
        pair = task_342dd610.generate(
            size=10, rows=[4, 5], cols=[4, 4], colors=[1, 2])
        self.assertEqual(pair["output"][4][5], 1)
        self.assertEqual(pair["output"][5][2], 2)
        self.assertEqual(sum(v != 8 for row in pair["output"] for v in row), 2)

    def test_noise_with_two_sliding_routes_is_rejected_in_every_orientation(self):
        rows = (
            "88800000080 80800008008 00808002000 08800082000 "
            "00088080000 00000080000 08000000080 00000000800 "
            "83800000000 83000000000 80000000800"
        )
        canvas = [list(map(int, row)) for row in rows.split()]
        for d4 in range(8):
            self.assertFalse(task_2dd70a9a._unique_slide_path(
                transformed(canvas, d4, list(range(10)))))

    def test_single_corner_route_is_valid_in_every_orientation(self):
        canvas = [[8] * 7 for _ in range(7)]
        for r, c in [(3, 1), (2, 1), (2, 2), (2, 3), (2, 4)]:
            canvas[r][c] = 0
        canvas[5][1] = canvas[4][1] = 3
        canvas[2][5] = canvas[2][6] = 2
        for d4 in range(8):
            self.assertTrue(task_2dd70a9a._unique_slide_path(
                transformed(canvas, d4, list(range(10)))))

    def test_blocked_route_is_rejected(self):
        canvas = [[8] * 7 for _ in range(7)]
        canvas[5][1] = canvas[4][1] = 3
        canvas[2][5] = canvas[2][6] = 2
        self.assertFalse(task_2dd70a9a._unique_slide_path(canvas))

    def test_supplied_fixture_bytes_unchanged(self):
        for module, digest in [
            (task_2dd70a9a, "fa7aac1928076a0091af36d0ee5aed9bf4b3ee9600d10356d05995a790b38a1b"),
            (task_342dd610, "3a5bdfa29736c328dbb91ebaed599f933c48543759eb58f61df50653b85b5061"),
        ]:
            actual = hashlib.sha256(json.dumps(
                module.validate(), sort_keys=True).encode()).hexdigest()
            self.assertEqual(actual, digest)


if __name__ == "__main__":
    unittest.main()

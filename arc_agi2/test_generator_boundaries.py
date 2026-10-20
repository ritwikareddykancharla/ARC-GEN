"""Regression cases for invalid dimensions and overwritten task evidence."""
import hashlib
import importlib
import json
import random
import unittest
from unittest.mock import patch

import common
from tasks import task_2b9ef948, task_39e1d7f9, task_538b439f


class GeneratorBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.random_state = random.getstate()
        random.seed(912)

    def tearDown(self):
        random.setstate(self.random_state)

    def sample_first_integer(self, generator, value):
        real_randint = common.randint
        first = True

        def choose(low, high):
            nonlocal first
            if first:
                first = False
                self.assertLessEqual(low, value)
                self.assertLessEqual(value, high)
                return value
            return real_randint(low, high)

        with patch.object(common, "randint", side_effect=choose):
            return generator()

    def test_all_logical_lattice_sizes_fit_arc(self):
        for size in range(5, 11):
            with self.subTest(size=size):
                pair = self.sample_first_integer(task_39e1d7f9.generate, size)
                for grid in pair.values():
                    self.assertLessEqual(len(grid), 30)
                    self.assertTrue(all(len(row) == len(grid) for row in grid))

    def test_eighteen_wide_reflection_scene_is_sampleable(self):
        for seed in range(20):
            random.seed(seed)
            pair = self.sample_first_integer(task_538b439f.generate, 18)
            for grid in pair.values():
                self.assertIn(18, (len(grid), len(grid[0])))
                self.assertTrue(all(len(row) == len(grid[0]) for row in grid))
            self.assertNotEqual(pair["input"], pair["output"])

    def test_path_inside_source_box_is_rejected(self):
        # Before the fix, this overwrote the centre and two box cells while
        # leaving the entire outer margin empty, erasing the rule's evidence.
        pair = task_2b9ef948.generate(
            width=14, height=21, color=3, brow=3, bcol=11,
            prow=3, pcol=12, turns=[-3])
        self.assertIsNone(pair["input"])
        self.assertIsNone(pair["output"])

    def test_path_endpoint_cannot_touch_source_box_margin(self):
        pair = task_2b9ef948.generate(
            width=20, height=20, color=3, brow=10, bcol=10,
            prow=10, pcol=5, turns=[4])
        self.assertIsNone(pair["input"])

    def test_original_fixture_bytes_unchanged(self):
        digests = {
            "39e1d7f9": "d9c72fdd0182df9d67e96c8993cd706530e7f6e7aaaccfa266cf52d21bc099ec",
            "538b439f": "fca0d1ad8fcd41da5facf43b7925553115fde0aa3416b4fac034488be379ea99",
            "2b9ef948": "ee5ce2158d51974b141e97c675a73dad1951668418be08dc10f6e0396a13510c",
        }
        for task, digest in digests.items():
            fixtures = importlib.import_module("tasks.task_" + task).validate()
            actual = hashlib.sha256(json.dumps(fixtures, sort_keys=True).encode()).hexdigest()
            with self.subTest(task=task):
                self.assertEqual(actual, digest)


if __name__ == "__main__":
    unittest.main()

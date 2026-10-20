"""Packing preserves object counts, spacing, and both sides of transformations."""
import hashlib
import itertools
import json
import random
import unittest
from unittest.mock import patch

import common
from arc_agi2.runtime import call, grid
from tasks import (task_22806e14, task_230f2e48, task_2753e76c, task_2c0b0aff,
                   task_37d3e8b2, task_48634b99, task_5e6bbc0b)


class BoundedPlacementTests(unittest.TestCase):
    def setUp(self):
        self.state = random.getstate()
        random.seed(872)

    def tearDown(self):
        random.setstate(self.state)

    def test_two_rectangle_feasibility_matches_exhaustive_search(self):
        for spacing in (0, 1):
            for w1, h1, w2, h2 in itertools.product(range(1, 4), repeat=4):
                feasible = any(
                    not common.overlaps([r1, r2], [c1, c2],
                                        [w1, w2], [h1, h2], spacing)
                    for r1 in range(4-h1) for c1 in range(4-w1)
                    for r2 in range(4-h2) for c2 in range(4-w2))
                result = common.place_rectangles(
                    3, 3, [w1, w2], [h1, h2], spacing, max_nodes=10000)
                self.assertEqual(result is not None, feasible)
                if result is not None:
                    self.assertFalse(common.overlaps(
                        *result, [w1, w2], [h1, h2], spacing))

    def test_impossible_or_budget_exhausted_pack_does_not_drop_objects(self):
        self.assertIsNone(common.place_rectangles(5, 5, [4, 4], [4, 4]))
        self.assertIsNone(common.place_rectangles(5, 5, [2], [2], max_nodes=0))

    def test_dense_plus_layout_retains_all_four(self):
        result = common.place_rectangles(7, 7, [3]*4, [3]*4, spacing=1)
        self.assertIsNotNone(result)
        self.assertEqual(len(result[0]), 4)
        self.assertFalse(common.overlaps(*result, [3]*4, [3]*4, 1))

    def test_seven_bending_segments_are_preserved(self):
        real, first = common.randint, True

        def choose(low, high):
            nonlocal first
            if first:
                first = False
                return 7
            return real(low, high)

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_230f2e48.generate, seconds=5)
        for canvas in pair.values():
            grid(canvas)
            self.assertEqual(sum(v == 5 for row in canvas for v in row), 7)
            self.assertEqual(sum(v == 0 for row in canvas for v in row), 7)

    def test_original_fixture_bytes_unchanged(self):
        cases = [
            (task_22806e14, "6678af53777d1ca253b66e063c0a4500ea4a9f6a22002fb4a5e91ffeb6089cf8"),
            (task_230f2e48, "e52e782e5f46db3a3ed7554fc0899fda8a6ff80faf8e2dc493a78da126421ca1"),
            (task_2753e76c, "4c92d337a762bb54c1d2c871f57b82c542593e5df2c23e9f5688909b7cadd9e9"),
            (task_2c0b0aff, "1da42be4ce97d89f390c6bc3bb96837916ad676c06f9fef09574f9dc5bdd014c"),
            (task_37d3e8b2, "ebff8b75533af00feea84511546876faa741a15a2b6c72b20575a5fbd1bdc91c"),
            (task_48634b99, "c6972e530e6c3d2b035cd414123f58f0dccd39d36630cc4b7885c0b72544578e"),
            (task_5e6bbc0b, "612569fb6909795e424fb46142b2d622ce1d8b1cf2e067c07f68d41c3cca54c2"),
        ]
        for module, digest in cases:
            actual = hashlib.sha256(json.dumps(
                module.validate(), sort_keys=True).encode()).hexdigest()
            self.assertEqual(actual, digest)

    def test_width_three_checkerboards_finish_for_every_height(self):
        real = common.randint
        for height in range(3, 10):
            dimensions = iter([3, height])

            def choose(low, high):
                return next(dimensions, None) or real(low, high)

            with patch.object(common, "randint", side_effect=choose):
                pair = call(task_5e6bbc0b.generate, seconds=1)
            for canvas in pair.values():
                grid(canvas)
                self.assertEqual(sum(v == 8 for row in canvas for v in row), 1)

    def test_fifteen_lines_are_preserved(self):
        settings = iter([1, 0, 15])
        real = common.randint

        def choose(low, high):
            value = next(settings, None)
            return real(low, high) if value is None else value

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_48634b99.generate, seconds=5)
        for canvas in pair.values():
            self.assertEqual(sum(v != 7 for row in canvas for v in row), 50)
            unseen = {(r, c) for r in range(16) for c in range(16)
                      if canvas[r][c] != 7}
            components = 0
            while unseen:
                stack = [unseen.pop()]
                components += 1
                while stack:
                    r, c = stack.pop()
                    for p in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                        if p in unseen:
                            unseen.remove(p)
                            stack.append(p)
            self.assertEqual(components, 15)


if __name__ == "__main__":
    unittest.main()

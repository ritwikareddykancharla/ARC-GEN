"""Random scenes must preserve the frame and distinguish instruction markers."""
import hashlib
import json
import random
import unittest
from unittest.mock import patch

import common
from arc_agi2.runtime import call
from tasks import task_4612dd53, task_465b7d93, task_fbf15a0b


class VisibleRoleSamplingTests(unittest.TestCase):
    def setUp(self):
        self.state = random.getstate()
        random.seed(184)

    def tearDown(self):
        random.setstate(self.state)

    def test_every_frame_length_preserves_its_full_boundary(self):
        for length in range(3, 9):
            for _ in range(10):
                real, first = common.randint, True

                def choose(low, high):
                    nonlocal first
                    if first:
                        first = False
                        return length
                    return real(low, high)

                with patch.object(common, "randint", side_effect=choose):
                    pair = call(task_465b7d93.generate, seconds=5)
                g = pair["input"]
                cells = [(r, c) for r, row in enumerate(g)
                         for c, v in enumerate(row) if v == 6]
                self.assertEqual(len(cells), 4 * length - 4)
                top, left = min(r for r, c in cells), min(c for r, c in cells)
                self.assertEqual(max(r for r, c in cells) - top + 1, length)
                self.assertEqual(max(c for r, c in cells) - left + 1, length)
                for r, row in enumerate(g):
                    for c, v in enumerate(row):
                        if v not in (6, 7):
                            self.assertFalse(top <= r < top + length
                                             and left <= c < left + length)

    def test_marker_colour_is_reserved_in_fresh_scenes(self):
        shapes = set()
        for _ in range(100):
            pair = call(task_fbf15a0b.generate, seconds=5)
            g, out = pair["input"], pair["output"]
            self.assertEqual(sum(v == 5 for row in g for v in row), 2)
            self.assertFalse(any(v == 5 for row in out for v in row))
            self.assertEqual(len({v for row in out for v in row}), 2)
            self.assertEqual(len(out) * len(out[0]) * 2, len(g) * len(g[0]))
            shapes.add((len(g), len(g[0])))
        self.assertGreater(len(shapes), 20)

    def test_cut_requires_two_interior_points_and_visible_frame_extrema(self):
        corners = [(2, 2), (2, 10), (8, 2), (8, 10)]
        for horizontal in (True, False):
            points = corners + [(5, 8)]
            args = (2, 2, 7, 9, 5 if horizontal else None,
                    None if horizontal else 8)
            self.assertFalse(task_4612dd53._visible_structure(
                points, [1] * len(points), *args))
            points += [(5, 7) if horizontal else (4, 8)]
            self.assertTrue(task_4612dd53._visible_structure(
                points, [1] * len(points), *args))
            self.assertFalse(task_4612dd53._visible_structure(
                points, [2, 2, 1, 1, 1, 1], *args))

    def test_all_supplied_lattices_satisfy_visibility_contract(self):
        for pairs in task_4612dd53.validate().values():
            for pair in pairs:
                points = [(r, c) for r, row in enumerate(pair["output"])
                          for c, v in enumerate(row) if v]
                colors = [pair["input"][r][c] for r, c in points]
                top, bottom = min(r for r, c in points), max(r for r, c in points)
                left, right = min(c for r, c in points), max(c for r, c in points)
                inner = [(r, c) for r, c in points
                         if top < r < bottom and left < c < right]
                horiz = inner[0][0] if inner and len({r for r, c in inner}) == 1 else None
                vert = inner[0][1] if inner and len({c for r, c in inner}) == 1 else None
                self.assertTrue(task_4612dd53._visible_structure(
                    points, colors, top, left, bottom-top+1, right-left+1, horiz, vert))

    def test_supplied_fixtures_unchanged(self):
        for module, digest in [
            (task_4612dd53, "70c51b512f42c583e2043c5d16a0b3bfdc6c15844c8a126946043a2d0e170d00"),
            (task_465b7d93, "03f507924240deda14522dc0f910cc3f3c84dc647e7c499825aee57a3be2a1ce"),
            (task_fbf15a0b, "bd8a0455cbc61c9f874c61cfbf10f8d6c25221589abed43244185f2a2eea52f5"),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(
                module.validate(), sort_keys=True).encode()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()

"""Regressions for hangs without reducing the requested scene complexity."""
import hashlib
import json
import random
import unittest
from unittest.mock import patch

import common
from arc_agi2.runtime import call
from tasks import (task_6bcdb01e, task_e57337a4, task_f0f8a26d,
                   task_ba9d41b8, task_ad38a9d0)
from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence


class BoundedSceneSamplingTests(unittest.TestCase):
    def setUp(self):
        self.random_state = random.getstate()
        random.seed(719)

    def tearDown(self):
        random.setstate(self.random_state)

    def test_rejected_marker_scene_is_discarded(self):
        # First scene has nine markers; second has exactly one.
        with patch.object(common, "randint", side_effect=[0]*27 + [0]*3 + [1]*8 + [0]):
            pair = task_e57337a4.generate()
        self.assertEqual(sum(v == 0 for row in pair["input"] for v in row), 1)
        self.assertEqual(sum(v == 0 for row in pair["output"] for v in row), 1)

    def test_ray_search_budget_does_not_reduce_turn_count(self):
        self.assertIsNone(task_6bcdb01e._sample_obstacles(10, 6, max_nodes=0))

    def test_ray_counts_and_painted_path_across_sizes(self):
        # Independent replay records all traversed cells and turn events.
        for size in range(5, 11):
            for count in range(3, 7):
                if (size, count) == (5, 6):
                    continue  # No feasibility claim for this combination.
                with self.subTest(size=size, count=count):
                    colors = task_6bcdb01e._sample_obstacles(size, count)
                    self.assertIsNotNone(colors)
                    pair = task_6bcdb01e.generate(
                        size=size, flip=0, flop=0, xpose=0, colors=colors)
                    self.assertIsNotNone(pair["input"])
                    walls = {(r, c) for r in range(size) for c in range(size)
                             if pair["input"][r][c] == 8}
                    path = {(1, 0), (1, 1)}
                    pos, direction, turns = (1, 2), (0, 1), 0
                    for _ in range(size * (count + 1) + 1):
                        r, c = pos
                        if not (0 <= r < size and 0 <= c < size):
                            break
                        self.assertNotIn(pos, walls)
                        path.add(pos)
                        dr, dc = direction
                        if (r+dr, c+dc) in walls:
                            sides = [(dc, -dr), (-dc, dr)]
                            available = [d for d in sides if (r+d[0], c+d[1]) not in walls]
                            self.assertEqual(len(available), 1)
                            direction = available[0]
                            turns += 1
                        pos = r + direction[0], c + direction[1]
                    else:
                        self.fail("Ray did not leave the grid")
                    self.assertEqual(turns, count)
                    painted = {(r, c) for r in range(size) for c in range(size)
                               if pair["output"][r][c] == 3}
                    self.assertEqual(painted, path)
                    self.assertEqual(
                        {(r, c) for r in range(size) for c in range(size)
                         if pair["output"][r][c] == 8}, walls)

    def test_rotating_lines_keep_requested_count_and_exact_shapes(self):
        for size in (7, 9, 11, 13):
            rows, cols, lengths, directions = call(
                lambda: task_f0f8a26d._sample_lines(size, size-4), seconds=5)
            self.assertEqual(len(rows), size-4)
            self.assertLessEqual(lengths.count(0), 1)
            before, after = set(), set()
            for r, c, length, vertical in zip(rows, cols, lengths, directions):
                self.assertTrue(0 <= length <= size//2 - 1)
                incoming = {(r+i, c) if vertical else (r, c+i)
                            for i in range(-length, length+1)}
                outgoing = {(r, c+i) if vertical else (r+i, c)
                            for i in range(-length, length+1)}
                self.assertFalse(incoming & before)
                self.assertFalse(outgoing & after)
                before.update(incoming)
                after.update(outgoing)
            pair = task_f0f8a26d.generate(
                size=size, color=2, rows=rows, cols=cols,
                lengths=lengths, cdirs=directions)
            for side, expected in (("input", before), ("output", after)):
                self.assertIsNotNone(pair[side])
                self.assertEqual(
                    {(r, c) for r in range(size) for c in range(size)
                     if pair[side][r][c] == 2}, expected)

    def test_supplied_fixture_hashes_unchanged(self):
        for module, expected in [
            (task_6bcdb01e, "23a1f3df0e4e45fee2fb6bcdeda19745324e1a2976c326fb88f25d1864584402"),
            (task_e57337a4, "091b64eb80f345a8736eca490cae7947d07138f419d7ff725e6efec0958c23b4"),
            (task_f0f8a26d, "969681a3d667f0d53341ee5a5b56fd0515c30d4d2a2123fe2b9278f7b8e2240c"),
            (task_ba9d41b8, "cf017bf46352f6a6495894b912dbebf84e232b6231be5c2aeca2544b5ee959f7"),
            (task_ad38a9d0, "b8011a499b3f01af9d248307a3c0aae9e15b2ec2c46e31ec41860cbc2630bb9a"),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(
                module.validate(), sort_keys=True).encode()).hexdigest(), expected)

    def test_impossible_initial_canvas_does_not_drop_checkerboard_boxes(self):
        settings, real = iter([12, 0, 4]), common.randint

        def choose(low, high):
            value = next(settings, None)
            return real(low, high) if value is None else value

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_ba9d41b8.generate, seconds=5)
        g = pair["input"]
        colors = {v for row in g for v in row} - {0}
        self.assertEqual(len(colors), 4)
        self.assertTrue(12 <= len(g[0]) <= 20)
        self.assertTrue(-2 <= len(g) - len(g[0]) <= 2)
        for color in colors:
            cells = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row)
                     if v == color}
            rs, cs = zip(*cells)
            height, width = max(rs)-min(rs)+1, max(cs)-min(cs)+1
            self.assertTrue(5 <= height <= 12 and 5 <= width <= 12)
            self.assertEqual(len(cells), height*width)

    def test_silhouette_sampler_keeps_all_six_types_and_two_extras(self):
        with patch.object(common, "randint", return_value=2):
            pair = call(task_ad38a9d0.generate, seconds=5)
        g = pair["input"]
        unseen = {(r, c) for r in range(9) for c in range(9) if g[r][c] == 6}
        components = []
        while unseen:
            group = {unseen.pop()}
            stack = list(group)
            while stack:
                r, c = stack.pop()
                for p in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                    if p in unseen:
                        unseen.remove(p)
                        group.add(p)
                        stack.append(p)
            components.append(group)
        self.assertEqual(len(components), 8)
        colors = []
        for group in components:
            output_colors = {pair["output"][r][c] for r, c in group}
            self.assertEqual(len(output_colors), 1)
            colors.extend(output_colors)
        self.assertEqual(set(colors), {2, 3, 4, 5, 8, 9})
        self.assertTrue(all(colors.count(c) <= 2 for c in colors))
        self.assertIsNone(task_ad38a9d0._sample_positions([2, 3, 4, 5, 8, 9], max_nodes=0))

    def test_checkerboard_query_needs_corner_evidence_in_every_orientation(self):
        odd = task_ba9d41b8.generate(
            width=12, height=12, wides=[5], talls=[5], rows=[1], cols=[2], colors=[3])
        even_width = task_ba9d41b8.generate(
            width=12, height=12, wides=[6], talls=[5], rows=[1], cols=[2], colors=[3])
        even_height = task_ba9d41b8.generate(
            width=12, height=12, wides=[5], talls=[6], rows=[1], cols=[2], colors=[3])
        palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
        for d4 in range(8):
            demos = [{k: transformed(p[k], d4, palette) for k in ("input", "output")}
                     for p in (odd, even_width, even_height)]
            # Query contains input only; no answer can affect this gate.
            query = [{"input": transformed(even_width["input"], d4, palette)}]
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence("ba9d41b8", demos[:1], query, palette, d4)
            require_colour_evidence("ba9d41b8", demos, query, palette, d4)


if __name__ == "__main__":
    unittest.main()

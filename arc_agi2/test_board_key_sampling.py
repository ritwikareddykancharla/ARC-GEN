"""Board placement preserves counts and excludes ambiguous key paintings."""
import hashlib
import json
import random
import unittest
from unittest.mock import patch

import common
from arc_agi2.runtime import call
from tasks import task_7d18a6fb, task_97a05b5b


class BoardKeySamplingTests(unittest.TestCase):
    def setUp(self):
        self.state = random.getstate()
        random.seed(381)

    def tearDown(self):
        random.setstate(self.state)

    def test_six_sprites_survive_an_initially_crowded_canvas(self):
        settings, real = iter([12, 12, 6]), common.randint

        def choose(low, high):
            value = next(settings, None)
            return real(low, high) if value is None else value

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_7d18a6fb.generate, seconds=5)
        g = pair["input"]
        self.assertTrue(12 <= len(g) <= 18 and 12 <= len(g[0]) <= 18)
        colors = {v for row in g for v in row} - {0, 1}
        self.assertEqual(len(colors), 6)
        board = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 1]
        top, left = min(r for r, c in board), min(c for r, c in board)
        self.assertIn(top, (0, len(g)-7))
        self.assertIn(left, (0, len(g[0])-7))
        self.assertEqual((len(pair["output"]), len(pair["output"][0])), (7, 7))
        for qy in (0, 4):
            for qx in (0, 4):
                color = g[top+qy+1][left+qx+1]
                cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row)
                         if v == color and not (top <= r < top+7 and left <= c < left+7)]
                y0, x0 = min(r for r, c in cells), min(c for r, c in cells)
                self.assertEqual(max(r for r, c in cells)-y0, 2)
                self.assertEqual(max(c for r, c in cells)-x0, 2)
                for dy in range(3):
                    for dx in range(3):
                        self.assertEqual(pair["output"][qy+dy][qx+dx], g[y0+dy][x0+dx])

    def test_five_keys_and_unique_painting_are_preserved(self):
        real, first = common.randint, True

        def choose(low, high):
            nonlocal first
            if first:
                first = False
                return 5
            return real(low, high)

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_97a05b5b.generate, seconds=5)
        self.assertEqual(len({v for row in pair["input"] for v in row} - {0, 2}), 5)
        self.assertEqual(len({v for row in pair["output"] for v in row} - {0, 2}), 5)
        self.assertEqual(task_97a05b5b._unique_output(pair["input"]),
                         tuple(map(tuple, pair["output"])))

    def test_translated_rotation_with_same_holes_is_rejected(self):
        # This S-shaped mask has a blank row. Rotating by 180 degrees and
        # shifting the key by one row preserves holes but changes its frame.
        pair = task_97a05b5b.generate(
            width=15, height=12, rows=[0, 0, 1, 1], cols=[0, 1, 1, 2],
            idxs=[0]*4, srows=[9], scols=[11], colors=[3],
            irows=[2], icols=[2], rotates=[0], wide=8, tall=8, brow=1, bcol=1)
        self.assertIsNone(task_97a05b5b._unique_output(pair["input"]))

    def test_supplied_key_fixtures_have_unique_exact_outputs(self):
        for pairs in task_97a05b5b.validate().values():
            for pair in pairs:
                self.assertEqual(task_97a05b5b._unique_output(pair["input"]),
                                 tuple(map(tuple, pair["output"])))
                self.assertIsNone(task_97a05b5b._unique_output(pair["input"], max_nodes=0))

    def test_fixture_hashes_unchanged(self):
        for module, digest in [
            (task_7d18a6fb, "c8628f1c8a3abb6336d82339a5f4221a213d1a950985c708c788d3726128aa78"),
            (task_97a05b5b, "78cdad91eeff2f7456aa1404f9e1acbabe33a9b02e527c4a9e783b8041d8a2d3"),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(
                module.validate(), sort_keys=True).encode()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()

import random
import unittest

from tasks import task_00d62c1b as generator
from .runtime import reference, solver, grid


class EnclosedGenerator(unittest.TestCase):
    def test_crowded_rectangles_finish_and_preserve_rule(self):
        import numpy as np
        from tasks import task_0d87d2a6
        from .runtime import call
        state = random.getstate()
        try:
            for seed in (211182452864934, 108026013769818, 14119720488996):
                random.seed(seed)
                pair = call(task_0d87d2a6.generate, seconds=5)
                self.assertEqual(grid(solver("0d87d2a6")(np.array(pair["input"]))),
                                 pair["output"])
        finally:
            random.setstate(state)
        original = reference("0d87d2a6")["canonical"]
        for split, pairs in task_0d87d2a6.validate().items():
            self.assertCountEqual(pairs, original[split])

    def test_quadrant_sampler_leaves_room_after_divider(self):
        from tasks import task_0bb8deee
        state = random.getstate()
        try:
            for seed in range(100):
                random.seed(seed)
                pair = task_0bb8deee.generate()
                grid(pair["input"])
                self.assertEqual(len(pair["output"]), 6)
                self.assertTrue(all(len(row) == 6 for row in pair["output"]))
        finally:
            random.setstate(state)
        original = reference("0bb8deee")["canonical"]
        for split, pairs in task_0bb8deee.validate().items():
            self.assertCountEqual(pairs, original[split])

    def test_incidental_three_cell_pocket_is_filled(self):
        state = random.getstate()
        try:
            random.seed(165269048030817)
            generator.generate()
            pair = generator.generate()
        finally:
            random.setstate(state)
        for row, col in ((8, 14), (9, 14), (9, 15)):
            self.assertEqual(pair["input"][row][col], 0)
            self.assertEqual(pair["output"][row][col], 4)
        self.assertEqual(grid(solver("00d62c1b")(pair["input"])), pair["output"])

    def test_original_fixture_labels_remain_exact(self):
        actual = generator.validate()
        expected = reference("00d62c1b")["canonical"]
        for split in ("train", "test"):
            self.assertCountEqual(actual[split], expected[split])

import random
import unittest

from tasks import task_00d62c1b as generator
from .runtime import reference, solver, grid


class EnclosedGenerator(unittest.TestCase):
    def test_band_sampler_keeps_arc_dimensions(self):
        from tasks import task_1190e5a7
        state = random.getstate()
        try:
            for seed in range(32):
                random.seed(seed)
                pair = task_1190e5a7.generate()
                grid(pair["input"])
                grid(pair["output"])
                self.assertLessEqual(len(pair["input"]), 30)
                self.assertLessEqual(len(pair["input"][0]), 30)
        finally:
            random.setstate(state)
        original = reference("1190e5a7")["canonical"]
        for split, pairs in task_1190e5a7.validate().items():
            self.assertCountEqual(pairs, original[split])

    def test_diagonal_does_not_wrap_via_negative_index(self):
        from tasks import task_1d61978c
        pair = task_1d61978c.generate(
            rows=[0, 8], cols=[0, 3], lengths=[2, 3], angles=[-1, 1])
        self.assertIsNone(pair["input"])
        self.assertIsNone(pair["output"])
        original = reference("1d61978c")["canonical"]
        for split, pairs in task_1d61978c.validate().items():
            self.assertCountEqual(pairs, original[split])

    def test_frame_bars_do_not_depend_on_absolute_column(self):
        from tasks import task_34cfa167
        crops = []
        for brow, bcol in ((1, 1), (1, 5), (5, 1)):
            pair = task_34cfa167.generate(
                width=30, height=30, wide=15, tall=15, length=2,
                brow=brow, bcol=bcol, colors=[0, 2, 4, 8])
            crops.append([row[bcol:bcol+15]
                          for row in pair["output"][brow:brow+15]])
            for r, row in enumerate(pair["output"]):
                for c, value in enumerate(row):
                    if not (brow <= r < brow+15 and bcol <= c < bcol+15):
                        self.assertEqual(value, 0)
        self.assertEqual(crops[0], crops[1])
        self.assertEqual(crops[0], crops[2])
        original = reference("34cfa167")["canonical"]
        for split, pairs in task_34cfa167.validate().items():
            self.assertCountEqual(pairs, original[split])

    def test_feasible_box_samplers_preserve_original_fixtures(self):
        from tasks import task_1c56ad9f, task_1e5d6875
        from .runtime import call
        state = random.getstate()
        try:
            for tid, module in (("1c56ad9f", task_1c56ad9f),
                                ("1e5d6875", task_1e5d6875)):
                for seed in range(32):
                    random.seed(seed)
                    pair = call(module.generate, seconds=5)
                    grid(pair["input"])
                    grid(pair["output"])
                original = reference(tid)["canonical"]
                for split, pairs in module.validate().items():
                    self.assertCountEqual(pairs, original[split])
        finally:
            random.setstate(state)

    def test_motif_sampler_uses_the_entire_nine_cell_input(self):
        from tasks import task_2072aba6
        state = random.getstate()
        positions = set()
        try:
            for seed in range(32):
                random.seed(seed)
                pair = task_2072aba6.generate()
                active = {(r, c) for r in range(3) for c in range(3)
                          if pair["input"][r][c] == 5}
                self.assertTrue(3 <= len(active) <= 6)
                positions.update(active)
        finally:
            random.setstate(state)
        self.assertEqual(positions, {(r, c) for r in range(3) for c in range(3)})
        original = reference("2072aba6")["canonical"]
        for split, pairs in task_2072aba6.validate().items():
            self.assertCountEqual(pairs, original[split])

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

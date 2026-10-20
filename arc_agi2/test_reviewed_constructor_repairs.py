"""Regression cases for defects exposed by fresh program verification."""
import unittest
import random
from unittest.mock import patch
from tasks import task_6ca952ad as falling
from tasks import task_7039b2d7 as panels
from tasks import task_78e78cff as leaking
from tasks import task_780d0b14 as patches
from tasks import task_855e0971 as strata
from tasks import task_6ffe8f07 as rays
from tasks import task_69889d6e as staircase
from tasks import task_b2862040 as holes
from tasks import task_c1d99e64 as full_lines
from tasks import task_db7260a4 as water
from .runtime import reference, call, grid


class ReviewedConstructorRepairs(unittest.TestCase):
    def test_top_border_contact_cannot_hide_two_objects(self):
        result = falling.generate(size=8, wides=[2, 3, 1], talls=[3, 1, 4],
                                  brows=[0, 0, 0], bcols=[1, 3, 7],
                                  colors='1110111111111',
                                  groups='0000001112222', fgcolor=5)
        self.assertIsNone(result['input'])

    def test_off_origin_leaks_preserve_opposite_frame(self):
        kwargs = dict(width=12, height=12, wide=5, tall=5, brow=5, bcol=5,
                      prow=7, pcol=7, colors=[0, 2, 8])
        right = leaking.generate(**kwargs, erows=[2], ecols=[4])
        self.assertEqual(right['output'][7][5], 2)
        self.assertEqual(right['output'][7][9:], [8, 8, 8])
        bottom = leaking.generate(**kwargs, erows=[4], ecols=[2])
        self.assertEqual(bottom['output'][5][7], 2)
        self.assertEqual([r[7] for r in bottom['output'][9:]], [8, 8, 8])

    def test_fixture_labels_unchanged(self):
        for tid, module in (('6ca952ad', falling), ('7039b2d7', panels),
                            ('78e78cff', leaking), ('780d0b14', patches),
                            ('855e0971', strata), ('6ffe8f07', rays),
                            ('69889d6e', staircase), ('b2862040', holes),
                            ('c1d99e64', full_lines), ('db7260a4', water)):
            for split, examples in module.validate().items():
                self.assertCountEqual(examples, reference(tid)['canonical'][split])

    def test_oversized_strata_seeds_now_fit_arc(self):
        state = random.getstate()
        try:
            for seed in (165084452629745, 227797453650026, 189404579730356):
                random.seed(seed)
                for _ in range(4):
                    pair = call(strata.generate, seconds=3)
                    grid(pair['input'])
                    grid(pair['output'])
        finally:
            random.setstate(state)

    def test_drop_validation_does_not_move_initial_drop(self):
        # The first simulation previously mutated pcol. The second simulation
        # then started from the wrong column and returned (None, None).
        state = random.getstate()
        try:
            random.seed(239)
            pair = water.generate()
            grid(pair['input'])
            grid(pair['output'])
            self.assertEqual(sum(c == 1 for c in pair['input'][0]), 1)
        finally:
            random.setstate(state)

    def test_exhaustion_does_not_silently_shrink_strata(self):
        with patch.object(strata.common, 'randint', return_value=10):
            with self.assertRaises(RuntimeError):
                strata._sample_heights(5)

    def test_noise_cannot_create_a_false_panel_divider(self):
        good = [[1, 1, 0, 2, 2], [1, 1, 0, 2, 2],
                [0, 0, 0, 0, 0],
                [3, 3, 0, 4, 4], [3, 3, 0, 4, 4]]
        self.assertTrue(patches._scene_ok(good, [2, 2], [2, 2], 5, 5))
        bad = [r[:] for r in good]
        bad[0] = [0]*5
        self.assertFalse(patches._scene_ok(bad, [2, 2], [2, 2], 5, 5))

    def test_crowded_ray_sampler_retains_requested_object_count(self):
        state = random.getstate()
        original = rays.common.randint
        try:
            for count in (4, 8, 12):
                random.seed(6100+count)
                def fixed_count(a, b):
                    return count if (a, b) == (4, 12) else original(a, b)
                with patch.object(rays.common, 'randint', side_effect=fixed_count):
                    widths, heights, rows, cols, colours = call(
                        lambda: rays._sample_scene(19, 19), seconds=10)
                self.assertEqual(len(widths), count)
                self.assertEqual(len(colours), count)
                self.assertFalse(rays.common.overlaps(rows, cols, widths, heights, 1))
                self.assertEqual(set(colours), {1, 2, 8})
        finally:
            random.setstate(state)

    def test_staircase_does_not_wrap_at_top_edge(self):
        # Both the climb and obstacle placement used to index row -1.
        for last in (0, 1):
            with self.assertRaises(ValueError):
                staircase.generate(vals=[0]*9+[last])
        # Reaching the top is legal; attempting another step is not.
        pair = staircase.generate(vals=[0]*9)
        self.assertEqual(pair['output'][0][9], 2)
        self.assertEqual(pair['output'][9][9], 0)

    def test_neighbor_barnacles_cannot_hide_a_closed_hole(self):
        # Two latent "open" boxes jointly seal the lower box's escape route.
        cells = set()
        for row, col in ((6, 2), (1, 3)):
            cells.update((r, c) for r in range(row, row+3)
                         for c in range(col, col+3)
                         if r in (row, row+2) or c in (col, col+2))
        cells.difference_update({(6, 3), (1, 4)})
        cells.update({(5, 2), (5, 4), (4, 3)})
        positions = sorted(cells)
        bad = (12, 12, [r for r, c in positions],
               [c for r, c in positions], [1]*len(positions))
        pair = holes._render(*bad)
        visible = holes._hole_rule_output(pair['input'], 9, 8)
        self.assertNotEqual(pair['output'], visible)
        self.assertEqual(visible[7][2], 8)  # Lower box borders the sealed hole.
        self.assertEqual(visible[4][3], 8)  # Upper box's attached protrusion.
        # Removing the bridging protrusion opens the route to the border.
        positions.remove((4, 3))
        good = (12, 12, [r for r, c in positions],
                [c for r, c in positions], [1]*len(positions))
        self.assertEqual(holes._render(*good)['output'],
                         holes._hole_rule_output(holes._render(*good)['input'], 9, 8))
        with patch.object(holes.common, 'randint', return_value=2):
            with patch.object(holes, '_sample_scene', side_effect=[bad, good]) as sample:
                self.assertEqual(holes.generate(), holes._render(*good))
                self.assertEqual([args.args for args in sample.call_args_list],
                                 [(2,), (2,)])

    def test_painted_line_cannot_create_an_unlabelled_noise_line(self):
        good = [(r+c) % 2 for r in range(10) for c in range(10)]
        bad = good[:]
        bad[:10] = [0, 1]+[0]*8
        # Both fields pass the old pre-paint two-colour test.
        for field in (bad, good):
            self.assertTrue(all(len(set(field[r*10:r*10+10])) == 2 for r in range(10)))
            self.assertTrue(all(len({field[r*10+c] for r in range(10)}) == 2 for c in range(10)))
        with patch.object(full_lines.common, 'randint',
                          side_effect=[10, 10, 1, 1]+bad+good):
            with patch.object(full_lines.common, 'sample', side_effect=[[3], [1]]) as sample:
                with patch.object(full_lines.common, 'random_color', return_value=1):
                    pair = full_lines.generate()
        # The first field was discarded; count and geometry were not resampled.
        self.assertEqual(sample.call_count, 2)
        self.assertEqual(pair['input'][0], [0, 0, 0, 1, 0, 1, 0, 1, 0, 1])
        for r in range(10):
            for c in range(10):
                self.assertEqual(pair['output'][r][c],
                                 2 if r == 3 or c == 1 else good[r*10+c])

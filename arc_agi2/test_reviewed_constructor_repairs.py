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
                            ('855e0971', strata), ('6ffe8f07', rays)):
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

"""Adversarial episode evidence cases for stamps, nubs and clipped beams."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from tasks import task_ac605cbb as stamps, task_dc2e9a9d as frames, task_db93a21d as beams


class SpatialEvidenceTests(unittest.TestCase):
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]

    def check(self, tid, weak, strong, query, agreed=None):
        for d4 in range(8):
            a = apply_episode(weak, d4, self.palette)
            b = apply_episode(strong, d4, self.palette)
            q = apply_episode([query], d4, self.palette)[0]
            with self.subTest(task=tid, d4=d4):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid, a, [{'input': q['input']}], self.palette, d4)
                require_colour_evidence(tid, a+b, [{'input': q['input']}], self.palette, d4)
                if agreed is not None:
                    same = apply_episode([agreed], d4, self.palette)[0]
                    require_colour_evidence(tid, a, [{'input': same['input']}], self.palette, d4)
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid, a, [{'input': q['input'], 'output': q['output']}], self.palette, d4)

    @staticmethod
    def single_stamp(ink):
        r, c = {1: (3, 3), 2: (3, 6), 3: (2, 3), 6: (8, 3)}[ink]
        return stamps.generate(size=11, rows=[r], cols=[c], colors=[ink])

    def test_each_query_seed_stamp_needs_evidence(self):
        a, b = self.single_stamp(1), self.single_stamp(2)
        self.check('ac605cbb', [a], [b], b, a)

    def test_seed_evidence_alone_does_not_teach_crossing(self):
        singles = [self.single_stamp(ink) for ink in (1, 2, 3, 6)]
        data = stamps.validate()
        self.check('ac605cbb', singles, data['train'], data['test'][0], singles[0])

    def test_clipped_crossing_does_not_teach_ray_direction(self):
        # Explicit border clipping outside the stricter random native domain:
        # crossing at the bottom-left gives only one yellow pixel, compatible
        # with down-left, up-left, down-right, or no propagation at all.
        g = [[0]*8 for _ in range(8)]
        g[7][3] = 2
        g[5][0] = 3
        out = [row[:] for row in g]
        out[6][0] = out[7][1] = out[7][2] = 5
        out[7][0] = 4
        clipped = {'input': g, 'output': out}
        singles = [self.single_stamp(ink) for ink in (1, 2, 3, 6)]
        data = stamps.validate()
        self.check('ac605cbb', singles+[clipped], data['train'], data['test'][0])

    @staticmethod
    def frame(angle):
        vertical = angle in (0, 2)
        return frames.generate(width=15, height=15, wides=[3 if vertical else 9],
                               talls=[9 if vertical else 3], brows=[2], bcols=[2], angles=[angle])

    def test_nub_axis_requires_its_own_copy_colour(self):
        a, b, q = self.frame(0), self.frame(1), self.frame(3)
        self.check('dc2e9a9d', [a], [b], q, a)

    def test_beamless_corner_does_not_teach_direction_or_colour(self):
        a = beams.generate(size=10, rows=[9], cols=[8], radii=[1])
        b = beams.generate(size=10, rows=[1], cols=[6], radii=[1])
        q = beams.generate(size=10, rows=[4], cols=[4], radii=[1])
        self.check('db93a21d', [a], [b], q, a)

    def test_canonical_demonstrations_are_sufficient(self):
        for tid, module in [('ac605cbb', stamps), ('dc2e9a9d', frames), ('db93a21d', beams)]:
            data = module.validate()
            for d4 in range(8):
                demos = apply_episode(data['train'], d4, self.palette)
                qs = apply_episode(data['test'], d4, self.palette)
                require_colour_evidence(tid, demos, [{'input': q['input']} for q in qs], self.palette, d4)

if __name__ == '__main__': unittest.main()

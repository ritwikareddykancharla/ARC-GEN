"""Counterexamples to hidden symmetry, shift and phase conventions."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.pattern_evidence import band_variants, shift_variants
from tasks import task_d56f2372 as shapes, task_caa06a1f as tiles, task_cad67732 as bands


class PatternEvidenceTests(unittest.TestCase):
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]

    def check(self, tid, weak, strong, query, agreed):
        for d4 in range(8):
            ds = apply_episode(weak, d4, self.palette)
            ss = apply_episode(strong, d4, self.palette)
            q, a = apply_episode([query, agreed], d4, self.palette)
            with self.subTest(task=tid, d4=d4):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid, ds, [{'input': q['input']}], self.palette, d4)
                require_colour_evidence(tid, ds+ss, [{'input': q['input']}], self.palette, d4)
                require_colour_evidence(tid, ds, [{'input': a['input']}], self.palette, d4)
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid, ds, [{'input': q['input'], 'output': q['output']}], self.palette, d4)

    def test_double_symmetry_demos_do_not_teach_selection_axis(self):
        weak = shapes.generate(width=12, height=12, shapes=[
            (1, 1, 1, ['101','010','101']), (2, 6, 6, ['110','001','101'])])
        query = shapes.generate(width=12, height=12, shapes=[
            (1, 1, 1, ['010','111','101']), (2, 6, 6, ['110','001','110'])])
        self.check('d56f2372', [weak], [query], query, weak)

    def test_query_can_eliminate_undefined_orthogonal_selection(self):
        weak = shapes.generate(width=12, height=12, shapes=[
            (1, 1, 1, ['101','010','101']), (2, 6, 6, ['110','001','101'])])
        query = shapes.generate(width=12, height=12, shapes=[
            (1, 1, 1, ['010','111','101']), (2, 6, 6, ['110','001','101'])])
        for d4 in range(8):
            a, q = apply_episode([weak, query], d4, self.palette)
            require_colour_evidence('d56f2372', [a], [{'input': q['input']}], self.palette, d4)

    def test_original_checkerboards_do_not_teach_three_colour_shift(self):
        data = tiles.validate()
        strong = tiles.generate(size=14, border=3, colors=[1,2,3], b=9)
        self.check('caa06a1f', data['train'], [strong], data['test'][0], data['train'][0])
        variants = shift_variants(data['test'][0]['input'])
        self.assertEqual(len({tuple(map(tuple, v)) for v in variants}), 3)
        self.assertEqual(variants[0], data['test'][0]['output'])

    def test_phase_evidence_must_be_on_same_band_axis(self):
        weak = bands.generate(size=5, diag=[1,2], offdiag=[3,4], flop=False)
        strong = bands.generate(size=7, diag=[1,2], offdiag=[3,4], flop=True)
        query = bands.generate(size=5, diag=[1,2], offdiag=[3,4], flop=True)
        agreed = bands.generate(size=6, diag=[1,2], offdiag=[3,4], flop=True)
        self.check('cad67732', [weak], [strong], query, agreed)

    def test_band_predictions_include_native_label_for_all_d4(self):
        for size in range(5,11):
            for diag, off in [([1,2],[0,3]), ([1,2,2],[3,3,4])]:
                for flop in (False,True):
                    pair = bands.generate(size=size, diag=diag, offdiag=off, flop=flop)
                    for d4 in range(8):
                        p = apply_episode([pair],d4,self.palette)[0]
                        self.assertIn(p['output'], band_variants(p['input'], self.palette[0]))

    def test_supplied_shape_and_band_episodes_pass(self):
        for tid, module in [('d56f2372', shapes), ('cad67732', bands)]:
            data = module.validate()
            for d4 in range(8):
                ds = apply_episode(data['train'],d4,self.palette)
                qs = apply_episode(data['test'],d4,self.palette)
                require_colour_evidence(tid,ds,[{'input':q['input']} for q in qs],self.palette,d4)

if __name__ == '__main__': unittest.main()

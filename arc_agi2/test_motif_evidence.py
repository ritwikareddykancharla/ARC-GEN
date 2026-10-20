"""Visible motif evidence, including clipped queries and the ring-corner marker."""
import copy
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from tasks import task_dfadab01 as gen


class MotifEvidenceTests(unittest.TestCase):
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]

    def gate(self, demos, query, should_pass):
        for d4 in range(8):
            ds = apply_episode(demos, d4, self.palette)
            q = apply_episode([query], d4, self.palette)[0]
            for extra in ({}, {'output': [[9]]}, {'output': q['output']}):
                with self.subTest(d4=d4, answer_attached=bool(extra)):
                    args = ('dfadab01', ds, [dict(input=q['input'], **extra)], self.palette, d4)
                    if should_pass: require_colour_evidence(*args)
                    else:
                        with self.assertRaises(MissingColourEvidence): require_colour_evidence(*args)

    def test_unseen_marker_needs_its_own_motif_and_colour(self):
        weak = gen.generate(width=10, height=10, markers=[(2, 2, 2)])
        strong = gen.generate(width=10, height=10, markers=[(2, 2, 5)])
        query = gen.generate(width=12, height=12, markers=[(6, 6, 5)])
        self.gate([weak], query, False)
        self.gate([weak, strong], query, True)

    def test_clipped_demo_cannot_teach_unobserved_interior_cells(self):
        clipped = gen.generate(width=10, height=10, markers=[(9, 9, 5)])
        full = gen.generate(width=10, height=10, markers=[(2, 2, 5)])
        self.gate([clipped], full, False)
        self.gate([clipped, full], full, True)

    def test_equally_clipped_query_needs_only_its_visible_cells(self):
        clipped = gen.generate(width=10, height=10, markers=[(9, 9, 5)])
        query = gen.generate(width=12, height=12, markers=[(11, 11, 5)])
        self.gate([clipped], query, True)

    def test_zero_only_clipped_query_does_not_require_hidden_paint_colour(self):
        clipped = gen.generate(width=10, height=10, markers=[(9, 9, 3)])
        query = gen.generate(width=12, height=12, markers=[(11, 11, 3)])
        self.gate([clipped], query, True)
        full = gen.generate(width=10, height=10, markers=[(2, 2, 3)])
        self.gate([clipped], full, False)

    def test_query_legend_teaches_unseen_marker_association(self):
        weak = gen.generate(width=10, height=10, markers=[(2, 2, 2)])
        query = gen.generate(width=12, height=12, markers=[(8, 8, 5)], legend=(1, 1, 5))
        self.gate([weak], query, True)

    def test_contradictory_observations_are_rejected(self):
        full = gen.generate(width=10, height=10, markers=[(2, 2, 5)])
        wrong = copy.deepcopy(full); wrong['output'][2][2] = 7
        self.gate([full, wrong], full, False)

    def test_unmatched_hole_blob_needs_erasure_demonstration(self):
        from tasks import task_e3721c99 as holes
        strong = holes.validate()['train'][0]
        inp = [row[:] for row in strong['input']]
        for r, row in enumerate(inp):
            for c, ink in enumerate(row):
                if ink == 5 and strong['output'][r][c] == 0: row[c] = 0
        weak = holes.generate(input_grid=inp)
        query = holes.validate()['test'][0]
        for d4 in range(8):
            a, b, q = apply_episode([weak, strong, query], d4, self.palette)
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('e3721c99', [a], [{'input': q['input']}], self.palette, d4)
            require_colour_evidence('e3721c99', [a, b], [{'input': q['input']}], self.palette, d4)
            require_colour_evidence('e3721c99', [a], [{'input': a['input']}], self.palette, d4)
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('e3721c99', [a], [{'input': q['input'], 'output': q['output']}], self.palette, d4)

    def test_ring_corner_marker_and_supplied_fixtures(self):
        data = gen.validate()
        for query in data['train']+data['test']:
            self.gate(data['train'], query, True)

if __name__ == '__main__': unittest.main()

import unittest
from .augmentation import apply_episode
from .colour_evidence import MissingColourEvidence, require_colour_evidence
from .program_targets import make_record


class ColourEvidenceTests(unittest.TestCase):
    def test_each_frame_size_needs_its_own_fill_mapping(self):
        def pair(side, offset=0):
            g = [[0]*(side+2) for _ in range(side+2)]
            out = [row[:] for row in g]
            for r in range(side):
                for c in range(side):
                    if r in (0, side-1) or c in (0, side-1):
                        g[r+offset][c+offset] = out[r+offset][c+offset] = 5
                    else:
                        out[r+offset][c+offset] = side+3
            return {'input': g, 'output': out}
        for d4 in range(8):
            pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            a, teacher, q = apply_episode([pair(3), pair(4), pair(4, 1)], d4, pal)
            query = {'input': q['input']}  # No query answer is needed.
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('c0f76784', [a], [query], pal, d4)
            require_colour_evidence('c0f76784', [a, teacher], [query], pal, d4)
            # An unchanged frame does not teach the interior fill colour.
            fake = dict(teacher, output=teacher['input'])
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('c0f76784', [a, fake], [query], pal, d4)

    def test_path_crossing_needs_a_changed_demo_cell(self):
        empty = {'input': [[2, 0, 0, 2]], 'output': [[2, 2, 2, 2]]}
        teacher = {'input': [[2, 1, 0, 2]], 'output': [[2, 3, 2, 2]]}
        query = {'input': [[2, 0, 1, 2]], 'output': [[2, 2, 3, 2]]}
        for d4 in range(8):
            pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            a, t, q = apply_episode([empty, teacher, query], d4, pal)
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('bcb3040b', [a], [{'input': q['input']}], pal, d4)
            require_colour_evidence('bcb3040b', [a, t], [{'input': q['input']}], pal, d4)
            # A 1 elsewhere in the image is not evidence for its path-crossing rule.
            off_path = {'input': [[2, 0, 0, 2], [1, 0, 0, 0]],
                        'output': [[2, 2, 2, 2], [1, 0, 0, 0]]}
            off = apply_episode([off_path], d4, pal)[0]
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('bcb3040b', [off], [{'input': q['input']}], pal, d4)

    def test_parity_rule_requires_relevant_demonstration(self):
        demo = {'input': [[1]*3 for _ in range(3)], 'output': [[1]*2]*2}
        query = {'input': [[1]*4 for _ in range(4)]}
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('a6953f00', [demo], [query])
        require_colour_evidence('a6953f00',
                                [dict(query, output=[[1]*2]*2)], [query])

    def test_chart_slot_needs_that_colour_in_demo_output(self):
        demo = {'input': [[5, 2]], 'output': [[5, 2, 7, 7, 7]]}
        query = {'input': [[8, 2]]}
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('aaecdb9a', [demo], [query])
        require_colour_evidence('aaecdb9a',
                                [demo, {'input': [[8]], 'output': [[7, 7, 8, 7, 7]]}],
                                [query])

    def test_overlay_priority_needs_observed_or_transitive_comparison(self):
        def pair(inks, winner):
            g = [[0]*9 for _ in range(9)]
            for k in range(9):
                g[4][k] = g[k][4] = 1
            for ink, (r, c) in zip(inks, ((0, 0), (0, 5), (5, 0), (5, 5))):
                g[r][c] = ink
            out = [[0]*4 for _ in range(4)]
            out[0][0] = winner
            return {'input': g, 'output': out}
        a, b, query = pair((7, 4), 7), pair((4, 8), 4), pair((7, 8), 7)
        for d4 in range(8):
            pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            x, y, q = apply_episode([a, b, query], d4, pal)
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('a68b268e', [x], [q], pal, d4)
            require_colour_evidence('a68b268e', [x, y], [q], pal, d4)

    def test_position_key_must_be_demonstrated_after_every_transform(self):
        from tasks import task_a834deea as gen
        demo = gen.generate(size=6, rows=[0], cols=[0],
                            colors=[0, 1, 1, 1, 1, 1, 1, 1, 1])
        query = gen.generate(size=6, rows=[1], cols=[1],
                             colors=[1, 0, 1, 1, 1, 1, 1, 1, 1])
        teacher = gen.generate(size=7, rows=[1], cols=[0],
                               colors=[0, 0, 1, 1, 1, 1, 1, 1, 1])
        for d4 in range(8):
            pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            a, b, t = apply_episode([demo, query, teacher], d4, pal)
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('a834deea', [a], [b], pal, d4)
            require_colour_evidence('a834deea', [a, t], [b], pal, d4)

    def test_clipped_diagonals_do_not_teach_unseen_colours(self):
        from tasks import task_a9f96cdd as gen
        demo, teacher, query = (gen.generate(row=r, col=c)
                                for r, c in ((0, 0), (1, 1), (1, 2)))
        for d4 in range(8):
            pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            a, t, b = apply_episode([demo, teacher, query], d4, pal)
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('a9f96cdd', [a], [b], pal, d4)
            require_colour_evidence('a9f96cdd', [a, t], [b], pal, d4)

    def test_solved_board_blank_rule_needs_example(self):
        from tasks import task_a416fc5b as gen
        demo = gen.generate(index=0, invert=0)
        teacher = gen.generate(index=1, invert=1)
        query = gen.generate(index=2, invert=1)
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('a416fc5b', [demo], [query])
        require_colour_evidence('a416fc5b', [demo, teacher], [query])

    def test_crop_fill_requires_visible_hole(self):
        solid = {'input': [[1, 1, 1], [1, 8, 8], [1, 8, 8]],
                 'output': [[8, 8], [8, 8]]}
        holed = {'input': [[1, 1, 1], [1, 8, 8], [1, 8, 1]],
                 'output': [[8, 8], [8, 0]]}
        for d4 in range(8):
            pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            a, b = apply_episode([solid, holed], d4, pal)
            with self.assertRaises(MissingColourEvidence):
                require_colour_evidence('a740d043', [a], [b], pal, d4)
            require_colour_evidence('a740d043', [a, b], [b], pal, d4)

    def test_missing_mask_mapping_rejected(self):
        demo = {'input': [[5, 0]], 'output': [[0, 4]]}
        query = {'input': [[8, 0]]}
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('6ea4a07e', [demo], [query])

    def test_fully_filled_demo_does_not_teach_mapping(self):
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('6ea4a07e',
                                    [{'input': [[8, 8]], 'output': [[0, 0]]}],
                                    [{'input': [[8, 0]]}])
        # A query with no complementary cells does not need the mapping.
        require_colour_evidence('6ea4a07e', [], [{'input': [[8, 8]]}])

    def test_ring_associations_survive_augmentation(self):
        demo = {'input': [[0, 0, 0], [0, 3, 0], [0, 0, 0]],
                'output': [[6, 6, 6], [6, 3, 6], [6, 6, 6]]}
        query = {'input': [[0, 3, 0]], 'output': [[6, 3, 6]]}
        for d4 in range(8):
            pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            a, b = apply_episode([demo, query], d4, pal)
            require_colour_evidence('913fb3ed', [a], [{'input': b['input']}],
                                    pal, d4)
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('913fb3ed', [demo], [{'input': [[8]]}])

    def test_motion_pair_needs_its_own_demonstration(self):
        demo = {'input': [[4, 0, 7]], 'output': [[4, 7, 0]]}
        query = {'input': [[1, 0, 8]], 'output': [[1, 8, 0]]}
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('494ef9d7', [demo], [{'input': query['input']}])
        for d4 in range(8):
            pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            a, b = apply_episode([demo, query], d4, pal)
            require_colour_evidence('494ef9d7', [a, b],
                                    [{'input': b['input']}], pal, d4)

    def test_export_cannot_bypass_evidence_check_with_query_label(self):
        for answer in ([[0, 2]], [[9, 9]]):
            with self.assertRaises(MissingColourEvidence):
                make_record({'task_id': '6ea4a07e',
                             'train': [{'input': [[5, 0]], 'output': [[0, 4]]}],
                             'test': [{'input': [[8, 0]]}],
                             'solutions': [answer]})

    def test_shape_legend_requires_query_shape_in_demos(self):
        from tasks import task_995c5fa3 as generator
        fixtures = generator.validate()
        # A known panel layout teaches no association for a novel hole mask.
        solid = [[5]*4 + [0] + [5]*4 + [0] + [5]*4 for _ in range(4)]
        unknown = [row[:] for row in solid]
        unknown[1][1] = 0
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('995c5fa3',
                                    [{'input': solid, 'output': [[2]*3]*3}],
                                    [{'input': unknown}])
        for d4 in range(8):
            pairs = apply_episode(fixtures['train'] + fixtures['test'],
                                  d4, list(range(10)))
            require_colour_evidence('995c5fa3', pairs[:-len(fixtures['test'])],
                                    [{'input': p['input']} for p in pairs[-len(fixtures['test']):]],
                                    d4=d4)

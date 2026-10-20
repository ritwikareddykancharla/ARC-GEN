"""Episode-level counterexamples without changing the single-pair domain."""
import copy
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import require_colour_evidence, MissingColourEvidence
from tasks import task_b0c4d837 as cup, task_e133d23d as union
from tasks import task_b27ca6d3 as domino, task_d94c3b52 as tiles


class EpisodeRoleEvidenceTests(unittest.TestCase):
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]

    def check(self, tid, weak, strong, query, agreed):
        for d4 in range(8):
            a, b, q, same = apply_episode([weak, strong, query, agreed], d4, self.palette)
            with self.subTest(task=tid, d4=d4):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid, [a], [{'input': q['input']}], self.palette, d4)
                require_colour_evidence(tid, [a, b], [{'input': q['input']}], self.palette, d4)
                require_colour_evidence(tid, [a], [{'input': same['input']}], self.palette, d4)
                # Gate decisions are independent of any attached query answer.
                for poisoned in ([[9]], None):
                    with self.assertRaises(MissingColourEvidence):
                        require_colour_evidence(tid, [a], [{'input': q['input'], 'output': poisoned}], self.palette, d4)

    def test_cup_fourth_cell_requires_demonstrated_turn(self):
        pair = lambda n: cup.generate(base=5, water=2, space=n, row_gap=1, col_gap=2)
        self.check('b0c4d837', pair(3), pair(4), pair(4), pair(3))

    def test_cup_first_cell_does_not_teach_line_direction(self):
        pair = lambda n: cup.generate(base=6, water=3, space=n, row_gap=2, col_gap=1)
        self.check('b0c4d837', pair(1), pair(2), pair(2), pair(1))

    def test_union_retains_blank_pairs_but_requires_paint_evidence(self):
        blank = union.generate(top=[0]*9, bottom=[0]*9)
        marked = union.generate(top=[1]+[0]*8, bottom=[0]*9)
        query = union.generate(top=[0]*9, bottom=[0, 1]+[0]*7)
        self.check('e133d23d', blank, marked, query, blank)

    def test_domino_retains_identity_pairs_but_requires_ring_colour(self):
        weak = domino.generate(width=6, height=6, rows=[1], cols=[1], colors=[2])
        strong = domino.validate()['train'][0]
        query = domino.validate()['test'][0]
        self.check('b27ca6d3', weak, strong, query, weak)

    def test_tile_fill_requires_actual_between_tile_evidence(self):
        strong = tiles.validate()['train'][0]
        query = tiles.validate()['test'][0]
        # Remove repeated template tiles to make a valid no-betweenness input
        # outside the random sampler's stricter nonempty-fill domain.
        weak = copy.deepcopy(strong)
        for g in [weak['input'], weak['output']]:
            for r, row in enumerate(g):
                for c in range(len(row)):
                    if not (1 <= r < 4 and 13 <= c < 16): row[c] = 0
        self.check('d94c3b52', weak, strong, query, weak)

    def test_canonical_episodes_satisfy_evidence_all_orientations(self):
        for tid, module in [('b0c4d837', cup), ('e133d23d', union),
                            ('b27ca6d3', domino), ('d94c3b52', tiles)]:
            data = module.validate()
            for d4 in range(8):
                demos = apply_episode(data['train'], d4, self.palette)
                qs = apply_episode(data['test'], d4, self.palette)
                require_colour_evidence(tid, demos, [{'input': q['input']} for q in qs], self.palette, d4)

if __name__ == '__main__': unittest.main()

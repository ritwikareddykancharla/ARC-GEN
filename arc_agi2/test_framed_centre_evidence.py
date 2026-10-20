"""Retain multiple agreeing rings; reject conflicting rings without latent tie breaks."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.framed_centre_evidence import framed_colours, require_framed_centre_evidence
from arc_agi2.direct_factories.task_d9fac9be import build_program
from tasks import task_d9fac9be as native


def rings(centres=(2, 3), answer=2, width=11, height=7):
    grid = [[0] * width for _ in range(height)]
    for x, colour in zip((2, 8), centres):
        ring = 3 if colour == 2 else 2
        for r in range(2, 5):
            for c in range(x - 1, x + 2):
                grid[r][c] = ring
        grid[3][x] = colour
    rows, cols, colours = [], [], []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                rows.append(r); cols.append(c); colours.append(value)
    return native.generate(width=width, height=height, rows=rows, cols=cols, colors=colours, center=answer)


class FramedCentreTests(unittest.TestCase):
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]

    def solve(self, d4, demonstrations, grid):
        namespace = {}; exec(build_program(d4, self.palette), namespace)
        return namespace['solve'](demonstrations, grid)

    def test_conflicting_rings_reject_under_all_augmentations(self):
        lesson, ambiguous = rings((2,), 2), rings()
        self.assertEqual(framed_colours(ambiguous['input'], list(range(10))), {2, 3})
        for d4 in range(8):
            demos = apply_episode([lesson], d4, self.palette)
            query = apply_episode([ambiguous], d4, self.palette)[0]
            for payload in (query, {'input': query['input']}, dict(query, output=[[99]])):
                with self.assertRaises(MissingColourEvidence):
                    require_framed_centre_evidence(demos, [payload], self.palette)
            with self.assertRaises(ValueError): self.solve(d4, demos, query['input'])

    def test_explicit_native_identical_input_has_two_possible_labels(self):
        first, second = rings(answer=2), rings(answer=3)
        self.assertEqual(first['input'], second['input'])
        self.assertNotEqual(first['output'], second['output'])

    def test_multiple_agreeing_rings_are_retained(self):
        lesson, query = rings((3,), 3), rings((2, 2), 2)
        for d4 in range(8):
            demos = apply_episode([lesson], d4, self.palette)
            q = apply_episode([query], d4, self.palette)[0]
            for payload in (q, {'input': q['input']}, dict(q, output=[[99]])):
                require_framed_centre_evidence(demos, [payload], self.palette)
            self.assertEqual(self.solve(d4, demos, q['input']), q['output'])

    def test_original_fixtures_including_touching_scatter(self):
        data = native.validate()
        for d4 in range(8):
            demos = apply_episode(data['train'], d4, self.palette)
            queries = apply_episode(data['test'], d4, self.palette)
            require_framed_centre_evidence(demos, queries, self.palette)
            for q in queries: self.assertEqual(self.solve(d4, demos, q['input']), q['output'])

    def test_no_ring_and_inconsistent_demos_reject(self):
        lesson = rings((2,), 2)
        bad = {'input': [[0] * 5 for _ in range(5)], 'output': [[0]]}
        for demos, query in (([], lesson), ([bad], lesson), ([dict(lesson, output=[[3]])], lesson), ([lesson], bad)):
            demos = apply_episode(demos, 0, self.palette)
            q = apply_episode([query], 0, self.palette)[0]
            with self.assertRaises(MissingColourEvidence): require_framed_centre_evidence(demos, [q], self.palette)
            with self.assertRaises(ValueError): self.solve(0, demos, q['input'])

    def test_ambiguous_demo_rejected_even_when_label_is_candidate(self):
        demos = apply_episode([rings()], 0, self.palette)
        q = apply_episode([rings((2,), 2)], 0, self.palette)[0]
        with self.assertRaises(MissingColourEvidence): require_framed_centre_evidence(demos, [q], self.palette)
        with self.assertRaises(ValueError): self.solve(0, demos, q['input'])


if __name__ == '__main__': unittest.main()

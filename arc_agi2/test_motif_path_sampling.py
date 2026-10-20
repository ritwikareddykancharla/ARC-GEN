"""Visible orientation, self-avoiding paths, and offset perimeter traversal."""
import hashlib
import json
import random
import unittest
from unittest.mock import patch

from arc_agi2.runtime import call
from tasks import task_36d67576 as motif, task_5792cb4d as path, task_ad173014 as perimeter
from tasks import task_ce8d95cc as lines, task_e7a25a18 as quadrant
from arc_agi2.direct_factories.task_e7a25a18 import build_program as quadrant_program


class MotifPathSamplingTests(unittest.TestCase):
    def setUp(self):
        self.state = random.getstate()
        random.seed(5792)

    def tearDown(self):
        random.setstate(self.state)

    def test_symmetric_core_requires_symmetric_decoration(self):
        points = [(0, 0, 2), (1, 0, 4), (0, 1, 4), (1, 1, 4),
                  (2, 0, 4), (0, 2, 4), (2, 1, 1)]
        self.assertFalse(motif._unambiguous_motif(*zip(*points)))
        points.append((1, 2, 1))
        self.assertTrue(motif._unambiguous_motif(*zip(*points)))

    def test_motif_sampler_retains_all_types_and_requested_colour_counts(self):
        for wide, tall in [(3, 3), (4, 2), (5, 1)]:
            for blue in (1, 2):
                for green in (1, 2, 3):
                    rows, cols, colors = motif._sample_motif(wide, tall, blue, green)
                    self.assertEqual([colors.count(c) for c in (4, 2, 1, 3)],
                                     [5, 1, blue, green])
                    self.assertEqual(len(set(zip(rows, cols))), len(colors))
                    self.assertTrue(motif._unambiguous_motif(rows, cols, colors))

    def test_canonical_motifs_satisfy_orientation_contract(self):
        original = motif.generate
        def inspect(**kw):
            self.assertTrue(motif._unambiguous_motif(kw['rows'], kw['cols'], kw['colors']))
            return original(**kw)
        with patch.object(motif, 'generate', side_effect=inspect):
            motif.validate()

    def test_paths_are_simple_and_output_reverses_every_visible_colour(self):
        for _ in range(100):
            pair = call(path.generate, seconds=5)
            g, out = pair['input'], pair['output']
            cells = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v != 8}
            self.assertGreaterEqual(len(cells), 7)
            neighbors = {p: [q for q in cells if abs(q[0]-p[0])+abs(q[1]-p[1]) == 1] for p in cells}
            ends = [p for p in cells if len(neighbors[p]) == 1]
            self.assertEqual(len(ends), 2)
            self.assertTrue(all(1 <= len(ns) <= 2 for ns in neighbors.values()))
            walk, prev, cur = [], None, ends[0]
            while cur is not None:
                walk.append(cur)
                nexts = [p for p in neighbors[cur] if p != prev]
                prev, cur = cur, nexts[0] if nexts else None
            self.assertEqual(len(walk), len(cells))
            self.assertEqual([out[r][c] for r, c in walk], [g[r][c] for r, c in reversed(walk)])

    def test_shifted_perimeter_includes_both_side_objects(self):
        pair = perimeter.generate(width=30, height=24, size=4,
            wide=16, tall=10, brow=8, bcol=6,
            rrows=[5, 10, 15, 10], rcols=[10, 19, 10, 3],
            colors=[3, 4, 6, 8], patterns='1' * 64)
        self.assertIsNotNone(pair['input'])
        for (r, c), before, after in zip([(6, 11), (11, 20), (16, 11), (11, 4)],
                                        [3, 4, 6, 8], [4, 6, 8, 3]):
            self.assertEqual(pair['input'][r][c], before)
            self.assertEqual(pair['output'][r][c], after)

    def test_nonsquare_line_scenes_compress_only_repeated_adjacent_rows_columns(self):
        import common
        for width, height in [(8, 13), (13, 8)]:
            for _ in range(25):
                values, real = iter([width, height]), common.randint
                def choose(low, high):
                    value = next(values, None)
                    return real(low, high) if value is None else value
                with patch.object(common, 'randint', side_effect=choose):
                    pair = lines.generate()
                g = pair['input']
                self.assertEqual((len(g), len(g[0])), (height, width))
                self.assertFalse(all(v != 0 for v in g[0]))
                self.assertFalse(all(v != 0 for v in g[-1]))
                self.assertFalse(all(row[0] != 0 for row in g))
                self.assertFalse(all(row[-1] != 0 for row in g))
                compressed = [row for i, row in enumerate(g) if i == 0 or row != g[i-1]]
                cols = list(zip(*compressed))
                cols = [c for i, c in enumerate(cols) if i == 0 or c != cols[i-1]]
                self.assertEqual(pair['output'], list(map(list, zip(*cols))))

    def test_quadrant_program_keeps_pattern_before_clearing_output(self):
        namespace = {}
        exec(quadrant_program(0, list(range(10))), namespace)
        for pair in quadrant.validate()['train'] + quadrant.validate()['test']:
            before = json.dumps(pair['input'])
            got = namespace['solve']([], pair['input'])
            self.assertEqual(got, pair['output'])
            self.assertEqual(json.dumps(pair['input']), before)
            self.assertEqual(len({v for row in got[1:-1] for v in row[1:-1]}), 4)

    def test_supplied_fixtures_unchanged(self):
        for module, digest in [
            (motif, '016a9a980616d5588a796949d35836ec693fd1b38ce6acb8e6b699ccc82879f7'),
            (path, 'e72c161c5f0159ff95af9e6c6073bbf3ca5e0100efed08b1035c6419bf2d0979'),
            (perimeter, 'c9fecd5eeb6d588ee1bfa6a56335b10e29eaf4e020173a1bd5d0ec391b4ac403'),
            (lines, '7a9a9b06ff669c3980938994c3521426b69ba372d41ab3069daf26c090ca63f9'),
            (quadrant, '9b30aa949994d6c2ded6c00357a020acdabd92b0b74ff9a08d59d1dc51e0589b'),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(module.validate(), sort_keys=True).encode()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()

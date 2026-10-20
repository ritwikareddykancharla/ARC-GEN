"""Require observable evidence for object associations and obstacle turns."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from tasks import task_ae3edfdc as flowers, task_e509e548 as letters, task_e5790162 as snake


class CategoryTurnEvidenceTests(unittest.TestCase):
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]

    def check(self, tid, weak, strong, query):
        for d4 in range(8):
            a, b, q = apply_episode([weak, strong, query], d4, self.palette)
            with self.subTest(task=tid, d4=d4):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid, [a], [{'input': q['input']}], self.palette, d4)
                require_colour_evidence(tid, [a, b], [{'input': q['input']}], self.palette, d4)
                require_colour_evidence(tid, [a], [{'input': a['input']}], self.palette, d4)
                # Even a forged query output cannot reveal a missing mapping.
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid, [a], [{'input': q['input'], 'output': q['output']}], self.palette, d4)

    def test_flower_colour_mapping_must_be_demonstrated(self):
        pair = lambda ds: flowers.generate(rows=[4, 10], cols=[3, 11], deltas=ds)
        weak = pair([1, -1, -1, -1, -1, -1, -1, -1])
        strong = pair([1, -1, -1, -1, 2, -1, -1, -1])
        query = pair([-1, -1, -1, -1, 3, -1, -1, -1])
        self.check('ae3edfdc', weak, strong, query)

    @staticmethod
    def letter(kind, shift=1):
        shapes = {
            'L': ([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)], 1),
            'U': ([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)], 6),
            'H': ([(0, 0), (1, 0), (2, 0), (1, 1), (0, 2), (1, 2), (2, 2)], 2),
        }
        pts, ink = shapes[kind]
        return letters.generate(width=10, height=10, rows=[r+shift for r, c in pts],
                                cols=[c+shift for r, c in pts], colors=[ink]*len(pts))

    def test_u_category_requires_colour_evidence(self):
        self.check('e509e548', self.letter('L'), self.letter('U'), self.letter('U', 5))

    def test_h_category_requires_colour_evidence(self):
        self.check('e509e548', self.letter('U'), self.letter('H'), self.letter('H', 5))

    def test_obstacle_colour_does_not_imply_opposite_colour_rule(self):
        weak = snake.generate(width=6, height=6, row=2, lengths=[3, 4], flip=False)
        strong = snake.generate(width=8, height=8, row=2, lengths=[4, 3, 4, 4], flip=False)
        query = snake.generate(width=6, height=6, row=3, lengths=[4, 3], flip=True)
        self.check('e5790162', weak, strong, query)

    def test_no_satellites_need_no_colour_mapping(self):
        pair = flowers.generate(rows=[4, 10], cols=[3, 11], deltas=[-1]*8)
        for d4 in range(8):
            a = apply_episode([pair], d4, self.palette)[0]
            require_colour_evidence('ae3edfdc', [a], [{'input': a['input']}], self.palette, d4)

    def test_dense_letter_packing_preserves_counts_sizes_and_optional_categories(self):
        import random
        from unittest.mock import patch
        import common
        saved = random.getstate()
        seen_types = []
        pack = common.place_rectangles
        sprite = common.rand_sprite
        def checked_pack(width, height, wides, talls, **kwargs):
            self.assertEqual(len(wides), 1 + max(height, width)//3)
            self.assertTrue(all(3 <= x <= 5 for x in wides+talls))
            self.assertEqual(kwargs['spacing'], 1)
            result = pack(width, height, wides, talls, **kwargs)
            if result is not None:
                self.assertFalse(common.overlaps(result[0], result[1], wides, talls, 1))
            return result
        def checked_sprite(kind, width, height):
            seen_types.append(kind)
            return sprite(kind, width, height)
        try:
            random.seed(67213375543451)
            with patch.object(common, 'place_rectangles', checked_pack), patch.object(common, 'rand_sprite', checked_sprite):
                pair = letters.generate()
            self.assertEqual((len(pair['input']), len(pair['input'][0])), (10, 9))
            self.assertEqual(len(seen_types), 4)
            self.assertNotIn('aitch', seen_types)  # no forced category mixture
        finally:
            random.setstate(saved)

    def test_letter_original_fixture_hash_is_unchanged(self):
        import hashlib, json
        self.assertEqual(hashlib.sha256(json.dumps(letters.validate(), sort_keys=True).encode()).hexdigest(),
                         '1e81ed2b82d43f73cceddf14d4a1fe4ad0a77ff66b08ba3baefd37b9b3304e8a')

    def test_all_supplied_demonstrations_suffice(self):
        for tid, module in [('ae3edfdc', flowers), ('e509e548', letters), ('e5790162', snake)]:
            data = module.validate()
            for d4 in range(8):
                demos = apply_episode(data['train'], d4, self.palette)
                qs = apply_episode(data['test'], d4, self.palette)
                require_colour_evidence(tid, demos, [{'input': q['input']} for q in qs], self.palette, d4)

if __name__ == '__main__': unittest.main()

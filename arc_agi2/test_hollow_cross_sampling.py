"""Reject visually hidden crosses without forbidding legal arm overlaps."""
import hashlib
import json
import unittest
from unittest.mock import patch

from tasks import task_f8be4b64 as generator


class HollowCrossSamplingTests(unittest.TestCase):
    def test_hidden_cross_changes_answer_without_changing_input(self):
        rows, cols, colors = [5, 7, 2], [5, 7, 10], [1, 2, 4]
        visible = generator.generate(14, rows, cols, colors)
        hidden = generator.generate(14, rows + [6], cols + [6], colors + [0])
        self.assertEqual(visible['input'], hidden['input'])
        self.assertEqual(visible['output'][2][6], 4)
        self.assertEqual(hidden['output'][2][6], 0)
        self.assertTrue(generator._identifiable_crosses(visible['input'], rows, cols, colors))
        self.assertFalse(generator._identifiable_crosses(hidden['input'], rows+[6], cols+[6], colors+[0]))

    def test_random_sampler_retries_hidden_cross_keeps_same_colours_and_size(self):
        colors = [1, 2, 4, 0]
        rows, cols = [2, 5, 8, 11], [2, 5, 8, 11]
        with patch.object(generator.common, 'randint', side_effect=[14, 4, 0]), \
                patch.object(generator.common, 'sample', side_effect=[colors, [5,7,2,6], [5,7,10,6], rows, cols]) as sample:
            pair = generator.generate()
        self.assertEqual(sample.call_count, 5)
        self.assertEqual(pair, generator.generate(14, rows, cols, colors))

    def test_identifiable_overlapping_arms_remain_allowed(self):
        rows, cols, colors = [5, 6], [5, 6], [1, 0]
        pair = generator.generate(14, rows, cols, colors)
        self.assertTrue(generator.common.overlaps(rows, cols, [3,3], [3,3]))
        self.assertTrue(generator._identifiable_crosses(pair['input'], rows, cols, colors))

    def test_original_fixtures_unchanged(self):
        digest = hashlib.sha256(json.dumps(generator.validate(), sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, '17d39a061c82ffca19e87697c73ff6cbc1696f108db3738e5710b6291d2eec16')


if __name__ == '__main__':
    unittest.main()

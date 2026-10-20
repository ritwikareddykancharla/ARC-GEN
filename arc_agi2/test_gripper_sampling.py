"""Regression for empty gripper halves without changing legal scenes."""
import hashlib
import json
import unittest
from unittest.mock import patch

from tasks import task_f8a8fe49 as generator


class GripperSamplingTests(unittest.TestCase):
    def test_empty_or_one_sided_draw_is_resampled(self):
        valid = [(0, 0), (0, 1), (1, 0), (1, 1),
                 (2, 0), (2, 1), (3, 0), (3, 1)]
        for invalid in ([], [(0, 0), (0, 1), (1, 0)], [(3, 0), (3, 1)]):
            # width=5, height=8, left=2, no transpose; preserve these choices
            # while retrying only the invalid content mask.
            with patch.object(generator.common, 'randint', side_effect=[5, 8, 2, 0]), \
                    patch.object(generator.common, 'random_pixels', side_effect=[invalid, valid]) as sample:
                pair = generator.generate()
            self.assertEqual(sample.call_count, 2)
            self.assertEqual(sum(v == 5 for row in pair['input'] for v in row), len(valid))
            self.assertEqual(sum(v == 5 for row in pair['output'] for v in row), len(valid))
            for y, x in valid:
                iy, ix = 5+y, 3+x
                spine = 3 if y < 2 else 10
                self.assertEqual(pair['input'][iy][ix], 5)
                self.assertEqual(pair['output'][2*spine-iy][ix], 5)

    def test_original_fixtures_unchanged(self):
        digest = hashlib.sha256(json.dumps(generator.validate(), sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, 'c3fa9cbd0159741a41dca447505cc257be7d9b7b88973fd6df046568ec0c29cc')


if __name__ == '__main__':
    unittest.main()

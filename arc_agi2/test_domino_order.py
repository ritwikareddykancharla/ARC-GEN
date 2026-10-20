"""Gravity labels must preserve pieces, independently of latent drawing order."""
import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from tasks import task_6ad5bdfd as generator
from .augmentation import transformed
from .direct_factories.task_6ad5bdfd import build_program


class DominoOrderTests(unittest.TestCase):
    def test_hidden_order_collision_and_physical_target(self):
        report = json.loads((Path(__file__).parent / 'reports' /
                             '6ad5bdfd-hidden-order-counterexample.json').read_text())
        far = generator.generate(**report['farther_first_parameters'])
        near = generator.generate(**report['nearest_first_parameters'])
        self.assertEqual(far, report['farther_first'])
        self.assertEqual(near, report['nearest_first'])
        self.assertEqual(far['input'], near['input'])
        self.assertNotEqual(far['output'], near['output'])
        for palette in [list(range(10)), [3,9,0,7,2,8,1,6,4,5]]:
            for d4 in range(8):
                ns = {}
                exec(build_program(d4, palette), ns)
                self.assertEqual(ns['solve']([], transformed(near['input'],d4,palette)),
                                 transformed(near['output'],d4,palette))

    def test_random_labels_preserve_all_colour_counts(self):
        checked = 0
        for seed in range(100):
            random.seed(seed)
            try:
                pair = generator.generate()
            except RuntimeError:
                continue
            self.assertEqual(Counter(v for row in pair['input'] for v in row),
                             Counter(v for row in pair['output'] for v in row))
            checked += 1
        self.assertGreaterEqual(checked, 90)

    def test_impossible_placement_has_bounded_rejection(self):
        with patch.object(generator.common, 'overlaps', return_value=True):
            with self.assertRaisesRegex(RuntimeError, 'placement retries exhausted'):
                generator.generate()

    def test_original_fixtures_unchanged(self):
        digest = hashlib.sha256(json.dumps(generator.validate(),sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, '9d599fa128a4801bdb81d2cdc8e247a5ae5931f3230c7ad8f22589a15d3cc4f9')


if __name__ == '__main__':
    unittest.main()

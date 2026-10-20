"""Directional supervision must be recoverable from visible demonstrations."""
import unittest

from .augmentation import exhaustive_variants, demonstrations_disambiguate


class AugmentationContextTests(unittest.TestCase):
    def test_symmetric_demos_cannot_label_a_direction(self):
        pairs = [
            {'input': [[1]], 'output': [[2]]},
            {'input': [[3]], 'output': [[4]]},
            {'input': [[5]], 'output': [[6]]},
            {'input': [[0, 0], [0, 0]], 'output': [[1, 0], [0, 0]]},
        ]
        self.assertFalse(demonstrations_disambiguate(exhaustive_variants(pairs)))

    def test_asymmetric_demonstration_supplies_direction(self):
        pairs = [
            {'input': [[1, 2], [3, 4]], 'output': [[1, 0], [0, 0]]},
            {'input': [[0, 0], [0, 0]], 'output': [[1, 0], [0, 0]]},
        ]
        self.assertTrue(demonstrations_disambiguate(exhaustive_variants(pairs)))

    def test_reordering_demonstrations_does_not_resolve_conflict(self):
        a = {'input': [[1]], 'output': [[2]]}
        b = {'input': [[3]], 'output': [[4]]}
        variants = [
            {'pairs': [a, b, {'input': [[0]], 'output': [[1]]}]},
            {'pairs': [b, a, {'input': [[0]], 'output': [[2]]}]},
        ]
        self.assertFalse(demonstrations_disambiguate(variants))

    def test_identical_answers_are_safe(self):
        pairs = [
            {'input': [[1]], 'output': [[2]]},
            {'input': [[0, 0], [0, 0]], 'output': [[1, 1], [1, 1]]},
        ]
        self.assertTrue(demonstrations_disambiguate(exhaustive_variants(pairs)))

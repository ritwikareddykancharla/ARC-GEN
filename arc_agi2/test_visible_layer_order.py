"""Layer order follows visible geometry, not an arbitrary palette priority."""
import hashlib
import json
import unittest

from tasks import task_68bc2e87 as generator
from .augmentation import transformed


class VisibleLayerOrderTests(unittest.TestCase):
    def render(self, boxes, order):
        return generator.generate(
            wides=[boxes[c][3] for c in order], talls=[boxes[c][2] for c in order],
            brows=[boxes[c][0] for c in order], bcols=[boxes[c][1] for c in order],
            colors=order)

    def test_consecutive_overlap_resolves_partial_visible_order(self):
        boxes = {7:(5,11,7,8), 2:(2,1,13,17), 6:(9,1,3,8), 9:(3,5,10,13)}
        order = [7,2,6,9]
        pair = self.render(boxes,order)
        for d4 in range(8):
            palette = [3,9,0,7,2,8,1,6,4,5]
            self.assertEqual(generator._visible_layer_order(transformed(pair['input'],d4,palette),palette[8]),
                             [palette[c] for c in order])

    def test_two_valid_latent_orders_with_same_input_are_rejected(self):
        boxes = {4:(2,4,16,14), 3:(3,12,9,7), 1:(3,3,11,12), 7:(2,6,14,12)}
        a, b = self.render(boxes,[4,3,1,7]), self.render(boxes,[3,4,1,7])
        self.assertEqual(a['input'],b['input'])
        self.assertNotEqual(a['output'],b['output'])
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError,'not uniquely evidenced'):
                generator._visible_layer_order(transformed(a['input'],d4,list(range(10))))

    def test_original_fixtures_unchanged(self):
        fixtures = generator.validate()
        digest = hashlib.sha256(json.dumps(fixtures,sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest,'b10bc9f82b6f62e2f6339c4062cbac006492aee3ea4c3eedc1f25004f2e5ca3b')
        for pair in fixtures['train'] + fixtures['test']:
            self.assertEqual(generator._visible_layer_order(pair['input']),sum(pair['output'],[]))


if __name__ == '__main__':
    unittest.main()

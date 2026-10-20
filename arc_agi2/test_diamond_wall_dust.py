"""A ray must stop on its first interior cell even if dust is wall-coloured."""
import unittest

from tasks import task_95755ff2 as generator
from .augmentation import transformed
from .direct_factories.task_95755ff2 import build_program


class DiamondWallDustTests(unittest.TestCase):
    def check_pair(self, pair):
        for palette in [list(range(10)), [3,9,0,7,2,8,1,6,4,5]]:
            for d4 in range(8):
                namespace = {}
                exec(build_program(d4, palette), namespace)
                self.assertEqual(namespace['solve']([], transformed(pair['input'],d4,palette)),
                                 transformed(pair['output'],d4,palette))

    def test_wall_coloured_first_interior_obstacle_blocks_entire_ray(self):
        pair = generator.generate(tops=[0,0,0,0,4], bottoms=[0]*5,
                                  rows=[2], cols=[6], color=2,
                                  flop=False, xpose=False)
        self.assertEqual([pair['output'][r][6] for r in range(2,9)], [2,0,0,0,0,0,0])
        self.check_pair(pair)

    def test_wall_coloured_legend_still_paints(self):
        pair = generator.generate(tops=[0,0,0,0,2], bottoms=[0]*5,
                                  rows=[], cols=[], color=4,
                                  flop=False, xpose=False)
        self.assertEqual([pair['output'][r][6] for r in range(2,9)], [2]*7)
        self.check_pair(pair)


if __name__ == '__main__':
    unittest.main()

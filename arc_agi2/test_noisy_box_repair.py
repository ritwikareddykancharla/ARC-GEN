"""Visible box geometry, output ambiguity, and historical fixture regressions."""
import hashlib
import json
from pathlib import Path
import unittest

from tasks import task_8731374e as boxes
from .augmentation import transformed
from .direct_factories.task_8731374e import build_program


PALETTE = [3,9,0,7,2,8,1,6,4,5]


def solve(grid, d4=0):
    namespace = {}
    exec(build_program(d4, PALETTE), namespace)
    return namespace['solve']([], transformed(grid, d4, PALETTE))


class NoisyBoxRepair(unittest.TestCase):
    def test_original_failure_all_orientations(self):
        data = json.loads((Path(__file__).parent/'reports/8731374e-execution-counterexample.json').read_text())
        episode = data['episode']
        pairs = episode['train'] + [dict(input=q['input'], output=o)
                                     for q,o in zip(episode['test'],episode['solutions'])]
        for pair in pairs:
            for d4 in range(8):
                self.assertEqual(solve(pair['input'], d4),
                                 transformed(pair['output'], d4, PALETTE))

    def test_largest_component_without_dots_is_not_the_box(self):
        grid = [[(r+c)%2 for c in range(20)] for r in range(20)]
        for r in range(10):
            for c in range(10): grid[r][c] = 7
        for r in range(12,18):
            for c in range(12,18): grid[r][c] = 3
        grid[14][14] = 2
        expected = [[2 if r==2 or c==2 else 3 for c in range(6)] for r in range(6)]
        for d4 in range(8):
            self.assertEqual(solve(grid,d4),transformed(expected,d4,PALETTE))

    def test_equal_area_different_outputs_are_rejected(self):
        grid = [[(r+c)%2 for c in range(11)] for r in range(7)]
        for col,colour,dot in [(1,3,2),(7,4,5)]:
            for r in range(2,5):
                for c in range(col,col+3): grid[r][c] = colour
            grid[3][col+1] = dot
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError,'unique largest'):
                solve(grid,d4)

    def test_noise_can_hide_the_latent_crop_width(self):
        grid = [[(r+c)%2 for c in range(10)] for r in range(10)]
        for r in range(1,7):
            for c in range(1,8): grid[r][c] = 3
        grid[3][3] = 2
        params = dict(width=10,height=10,tall=6,rowoffset=1,coloffset=1,
                      rows=[2],cols=[2],colors=sum(grid,[]))
        small = boxes.generate(wide=6,**params)
        large = boxes.generate(wide=7,**params)
        self.assertEqual(small['input'],large['input'])
        self.assertNotEqual(small['output'],large['output'])
        self.assertNotEqual(boxes._box_outputs(grid),{tuple(map(tuple,small['output']))})
        self.assertEqual(boxes._box_outputs(grid),{tuple(map(tuple,large['output']))})
        for d4 in range(8):
            self.assertEqual(solve(grid,d4),transformed(large['output'],d4,PALETTE))

    def test_original_fixtures_unchanged(self):
        digest = hashlib.sha256(json.dumps(boxes.validate(),sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest,'d6ba9c6a9717436554222e6791dd30c33ac3b47641abfe2ad3856827da36789e')


if __name__ == '__main__':
    unittest.main()

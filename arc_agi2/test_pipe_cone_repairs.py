"""Recover broken cone arms and reject invisible pipe-order tie breaking."""
import hashlib
import json
from pathlib import Path
import unittest

import common
from tasks import task_b9630600 as pipes, task_896d5239 as cones
from .augmentation import transformed
from .direct_factories.task_b9630600 import build_program as pipe_program
from .direct_factories.task_896d5239 import build_program as cone_program


REPORTS = Path(__file__).parent/'reports'
PALETTE = [3,9,0,7,2,8,1,6,4,5]


def namespace(factory,d4):
    ns = {}
    exec(factory(d4,PALETTE),ns)
    return ns


class PipeConeRepairs(unittest.TestCase):
    def test_pipe_order_is_invisible_and_changes_output(self):
        witness=json.loads((REPORTS/'b9630600-hidden-order-witness.json').read_text())
        first=pipes.generate(**witness['first']['parameters'])
        second=pipes.generate(**witness['second']['parameters'])
        self.assertEqual(first,witness['first']['pair'])
        self.assertEqual(second,witness['second']['pair'])
        self.assertEqual(first['input'],second['input'])
        self.assertNotEqual(first['output'],second['output'])
        p=witness['first']['parameters']
        self.assertFalse(pipes._visibly_determined(p['wides'],p['talls'],p['brows'],p['bcols'],first['input']))
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError,'unique minimum spanning tree'):
                namespace(pipe_program,d4)['solve']([],transformed(first['input'],d4,PALETTE))

    def test_equal_lengths_are_allowed_without_competing_trees(self):
        self.assertTrue(pipes._unique_spanning_tree(4,[(1,0,1),(1,1,2),(1,2,3),(5,0,3)]))
        self.assertFalse(pipes._unique_spanning_tree(4,[(1,0,1),(1,1,2),(1,2,3),(1,0,3)]))
        self.assertFalse(pipes._unique_spanning_tree(4,[(1,0,1),(1,2,3)]))

    def test_clear_pipe_lines_can_enclose_a_box(self):
        wides,talls,brows,bcols=[5,5,3],[11,11,3],[0,0,4],[0,20,10]
        grid=common.grid(30,30)
        for w,h,r,c in zip(wides,talls,brows,bcols):
            common.hollow_rect(grid,w,h,r,c,3)
        candidates=pipes._box_candidates(wides,talls,brows,bcols,grid)
        self.assertIn((16,0,1,True),candidates)
        self.assertTrue(any(grid[r][c] for r in range(1,10) for c in range(5,20)))
        self.assertTrue(pipes._visibly_determined(wides,talls,brows,bcols,grid))

    def test_disconnected_cone_arm_counterexample(self):
        data=json.loads((REPORTS/'896d5239-execution-counterexample.json').read_text())
        e=data['episode']
        pairs=e['train']+[dict(input=q['input'],output=o) for q,o in zip(e['test'],e['solutions'])]
        # The saved example already has a palette; compose the extra palette.
        composed=[PALETTE[x] for x in data['palette']]
        for pair in pairs:
            for d4 in range(8):
                ns={};exec(cone_program(d4,composed),ns)
                self.assertEqual(ns['solve']([],transformed(pair['input'],d4,PALETTE)),
                                 transformed(pair['output'],d4,PALETTE))

    def test_clipped_fixture_cones_all_orientations(self):
        pair=cones.validate()['test'][0]
        for d4 in range(8):
            self.assertEqual(namespace(cone_program,d4)['solve']([],transformed(pair['input'],d4,PALETTE)),
                             transformed(pair['output'],d4,PALETTE))

    def test_cone_search_exhaustion_is_explicit(self):
        ns=namespace(cone_program,0);ns['_NODE_BUDGET']=0
        with self.assertRaisesRegex(RuntimeError,'search budget exhausted'):
            ns['solve']([],transformed(cones.validate()['test'][0]['input'],0,PALETTE))

    def test_one_sided_cone_does_not_silently_return_input(self):
        grid=[[0]*7 for _ in range(7)]
        for r,c in [(1,1),(2,2),(3,3)]:grid[r][c]=3
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError,'unique cone completion'):
                namespace(cone_program,d4)['solve']([],transformed(grid,d4,PALETTE))

    def test_original_fixtures_unchanged(self):
        for module,expected in [(pipes,'cc5c9ada93b8243dbe0648bfce5362e1283f8542ed2d47d46456d08df8ae3caf'),
                                (cones,'001b7e873788eacfa3324ed3274d79e99d597947b71597181a6683df10074608')]:
            self.assertEqual(hashlib.sha256(json.dumps(module.validate(),sort_keys=True).encode()).hexdigest(),expected)


if __name__=='__main__':
    unittest.main()

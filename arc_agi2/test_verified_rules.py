"""Independent evidence for complete-chain verification over greedy matching."""
import copy
import importlib
import itertools
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from .runtime import reference, solver, verification_solver, grid


class CompleteChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module=importlib.import_module('tasks.task_78332cb0')
        cls.old=staticmethod(solver('78332cb0'))
        cls.solve=staticmethod(verification_solver('78332cb0'))

    def test_canonical_and_every_panel_permutation(self):
        original=reference('78332cb0')['canonical']
        for p in original['train']+original['test']:
            self.assertEqual(self.solve(p['input']),p['output'])
        p=original['train'][2]
        panels=[[row[6*i:6*i+5] for row in p['input']] for i in range(3)]
        failures=0
        for order in itertools.permutations(range(3)):
            a=[panels[order[0]][r]+[6]+panels[order[1]][r]+[6]+panels[order[2]][r]
               for r in range(5)]
            self.assertEqual(self.solve(a),p['output'])
            failures+=grid(self.old(a))!=p['output']
            transpose=lambda a:[list(r) for r in zip(*a)]
            self.assertEqual(self.solve(transpose(a)),transpose(p['output']))
        self.assertEqual(failures,3)

    def test_random_generator_can_require_backtracking(self):
        for seed in range(20):
            random.seed(seed)
            p=self.module.generate(rows=1,cols=3,height=5,width=5,vertical=True,
                                   order=[0,2,1],colors=[8,9,1],repeat_contacts=True)
            self.assertEqual(self.solve(p['input']),p['output'])
            self.assertNotEqual(grid(self.old(p['input'])),p['output'])

    def test_nonadjacent_repeat_detour(self):
        for vertical in (False,True):
            order=[3,2,0,1]
            edges=[(None,1),(1,2),(2,1),(1,None)]
            slots=[None]*4
            for slot,(entry,exit) in zip(order,edges):
                random.seed(slot)
                cells=self.module._shape(5,5,entry,exit,0)
                if not vertical:cells={(x,y) for y,x in cells}
                slots[slot]=[''.join('x' if (y,x) in cells else '.' for x in range(5))
                             for y in range(5)]
            p=self.module.generate(rows=2,cols=2,height=5,width=5,vertical=vertical,
                                   order=order,colors=[1,2,3,4],bitmaps=slots)
            self.assertEqual(self.solve(p['input']),p['output'])
            self.assertNotEqual(grid(self.old(p['input'])),p['output'])

    def test_ambiguous_order_and_invalid_controls_are_rejected(self):
        canonical=reference('78332cb0')['canonical']['train'][2]['input']
        start=[r[:5] for r in canonical]
        end=[r[12:] for r in canonical]
        a=[start[y]+[6]+[7,7,1,7,7]+[6]+[7,7,2,7,7]+[6]+end[y]
           for y in range(5)]
        with self.assertRaisesRegex(ValueError,'unique complete chain'):
            self.solve(a)
        for kwargs in ({'vertical':1},{'repeat_contacts':'yes'},{'rows':7},
                       {'colors':[True,2,3]},{'order':[False,1,2]},
                       {'rows':2,'cols':2,'height':20,'width':20}):
            with self.assertRaises(ValueError):self.module.generate(**kwargs)

    def test_pool_builder_uses_improved_verifier(self):
        from . import build_million as builder
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(builder,'OUT',Path(tmp)),patch.object(builder,'POOL_SIZE',24):
                report=builder.make_pool('78332cb0')
                self.assertEqual(report['pairs'],24)
                self.assertNotIn('reference_disagreement',report['rejections'])
                rows=pq.read_table(Path(tmp)/'pools/78332cb0.parquet').to_pylist()
                self.assertTrue(any(grid(self.old(p['input']))!=p['output'] for p in rows))
                for p in rows:self.assertEqual(self.solve(p['input']),p['output'])


if __name__=='__main__':unittest.main()

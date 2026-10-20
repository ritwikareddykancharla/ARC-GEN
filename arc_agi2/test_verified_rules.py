"""Independent evidence for documented verifier improvements."""
import copy
import importlib
import itertools
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from .runtime import reference, solver, verification_solver, grid


class CommutingGapTests(unittest.TestCase):
    def test_fourteen_independent_gaps_have_one_completed_grid(self):
        """Equal-distance commuting links must not exhaust tie enumeration."""
        module = importlib.import_module('tasks.task_f8f52ecc')
        pair = module.generate(
            height=5, width=30,
            chains=[(2, [(2, 0), (2, 28)],
                     [(2, col) for col in range(0, 29, 2)])])
        expected = [[1] * 30 for _ in range(5)]
        expected[2][:29] = [2] * 29
        self.assertEqual(pair['output'], expected)
        self.assertEqual(grid(verification_solver('f8f52ecc')(pair['input'])),
                         expected)
        self.assertEqual(sum(value == 2 for row in pair['input'] for value in row),
                         15)


class LegendAndPointReflectionTests(unittest.TestCase):
    def test_corner_divider_does_not_become_a_zero_hole_key(self):
        module = importlib.import_module('tasks.task_e3721c99')
        for seed, side in enumerate(('top', 'bottom', 'left', 'right'), 12300):
            random.seed(seed)
            pair = module.generate(
                width=30, height=30, divider='corner', side=side,
                key_holes=[0, 2], key_colours=[3, 4],
                blob_holes=[0, 2, 3])
            painted = {pair['output'][y][x]
                       for y, row in enumerate(pair['input'])
                       for x, value in enumerate(row) if value == 5}
            self.assertEqual(painted, {0, 3, 4})
            for y, row in enumerate(pair['input']):
                for x, value in enumerate(row):
                    if value != 5:
                        self.assertEqual(pair['output'][y][x], value)

    def test_only_single_key_colour_holes_fill(self):
        module = importlib.import_module('tasks.task_dbff022c')
        pair = module.generate(
            width=18, height=16, legend_side='top', legend_offset=2,
            keys=[2, 3, 4], fills=[6, 7, 8],
            shapes=[
                (4, 2, 2, ['###', '#o#', '###']),
                (4, 7, 9, ['###', '#o#', '###']),
                (9, 7, 2, ['#%#', '#o#', '###'], 3)])
        expected = copy.deepcopy(pair['input'])
        expected[5][3] = 6
        self.assertEqual(pair['output'], expected)
        self.assertEqual(expected[5][8], 0)  # Non-key outline.
        self.assertEqual(expected[10][8], 0)  # Two-colour outline.

    def test_marker_rotation_is_not_plain_mirroring(self):
        module = importlib.import_module('tasks.task_e729b7be')
        pair = module.generate(
            size=11, top=2,
            rows=['....1', '...22', '...31', '....2', '....3'])
        expected = copy.deepcopy(pair['input'])
        mirror = copy.deepcopy(pair['input'])
        for y, row in enumerate(pair['input']):
            for x, colour in enumerate(row):
                if colour not in (7, 4, 8):
                    expected[10-y][10-x] = colour
                    mirror[y][10-x] = colour
        self.assertEqual(pair['output'], expected)
        self.assertNotEqual(pair['output'], mirror)

    def test_disconnected_marker_touching_shape_rejected(self):
        module = importlib.import_module('tasks.task_e729b7be')
        with self.assertRaises(ValueError):
            module.generate(size=9, top=3, rows=['...1', '.2.1', '...3'])


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



class CroppedMosaicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module=importlib.import_module('tasks.task_de493100')
        cls.old=staticmethod(solver('de493100'))
        cls.solve=staticmethod(verification_solver('de493100'))

    def test_canonical_replay_and_all_supported_sizes(self):
        original=reference('de493100')['canonical']
        self.assertEqual(self.module.validate(),original)
        for pair in original['train']+original['test']:
            self.assertEqual(self.solve(pair['input']),pair['output'])
            self.assertEqual(grid(self.old(pair['input'])),pair['output'])
        for size in range(12,31,2):
            random.seed(70000+size)
            pair=self.module.generate(size=size)
            self.assertEqual(len(pair['input']),size)
            self.assertEqual(self.solve(pair['input']),pair['output'])

    def test_saved_counterexample_and_inconsistent_orbit(self):
        import json
        evidence=json.loads((Path(__file__).parent/'reports/review-blockers/de493100.json').read_text())['counterexample']
        self.assertEqual(self.solve(evidence['input']),evidence['output'])
        self.assertNotEqual(grid(self.old(evidence['input'])),evidence['output'])
        bad=copy.deepcopy(reference('de493100')['canonical']['test'][0]['input'])
        bad[2][2]=next(v for v in [0,1,2,3,4,5,6,8,9] if v!=bad[2][2])
        with self.assertRaisesRegex(ValueError,'Visible reflection partners disagree'):
            self.solve(bad)

    def test_partial_mask_controls_and_unrecoverable_scene(self):
        for seed in range(5):
            random.seed(seed)
            pair=self.module.generate(mask_height=14,mask_width=14)
            self.assertEqual(len(pair['input']),30)
            self.assertEqual((len(pair['output']),len(pair['output'][0])),(14,14))
            self.assertEqual(self.solve(pair['input']),pair['output'])
        pair=self.module.generate(size=12,mask_height=1,mask_width=1)
        self.assertEqual((len(pair['output']),len(pair['output'][0])),(1,1))
        self.assertEqual(self.solve(pair['input']),pair['output'])
        q=[[1+(r+c)%2 for c in range(7)] for r in range(7)]
        with self.assertRaisesRegex(ValueError,'no valid visible reconstruction cue'):
            self.module.generate(quadrant=q,mask=[0,0,2,2])
        for kwargs in [{'size':True},{'size':13},{'size':18.0},{'mask_height':True}]:
            with self.assertRaises(ValueError):self.module.generate(**kwargs)

    def test_pool_builder_retains_variable_sizes(self):
        from . import build_million as builder
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(builder,'OUT',Path(tmp)),patch.object(builder,'POOL_SIZE',24):
                report=builder.make_pool('de493100')
                self.assertEqual(report['pairs'],24)
                self.assertNotIn('reference_disagreement',report['rejections'])
                rows=pq.read_table(Path(tmp)/'pools/de493100.parquet').to_pylist()
                self.assertGreater(len({len(p['input']) for p in rows}),1)
                for pair in rows:self.assertEqual(self.solve(pair['input']),pair['output'])

if __name__=='__main__':unittest.main()

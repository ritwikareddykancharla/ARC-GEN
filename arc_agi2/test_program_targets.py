import copy
import unittest
from .augmentation import transformed
from .runtime import reference
from .program_targets import compile_target, audit_target, verify, make_record, TargetError, clean

class ProgramTargets(unittest.TestCase):
    def test_empty_box_examples_rejected_even_when_program_is_exact(self):
        for role in ('train', 'test'):
            ep = self.episode('00dbd492')
            blank = [[6] * 7 for _ in range(7)]
            ep[role][0]['input'] = blank
            if role == 'train':
                ep['train'][0]['output'] = blank
            else:
                ep['solutions'][0] = blank
            with self.assertRaisesRegex(TargetError, 'background-only'):
                make_record(ep)

    def test_smallest_box_sampler_is_nonempty(self):
        import random
        from unittest.mock import patch
        from tasks import task_00dbd492
        original = task_00dbd492.common.randint
        def smallest_canvas(a, b):
            return 7 if (a, b) == (7, 23) else original(a, b)
        state = random.getstate()
        try:
            for seed in range(20):
                random.seed(seed)
                with patch.object(task_00dbd492.common, 'randint', smallest_canvas):
                    pair = task_00dbd492.generate()
                self.assertEqual(len(pair['input']), 7)
                self.assertEqual(len({v for row in pair['input'] for v in row}), 2)
                self.assertNotEqual(pair['input'], pair['output'])
        finally:
            random.setstate(state)

    def test_box_can_have_more_outline_than_background(self):
        from tasks import task_00dbd492
        pair = task_00dbd492.generate(size=7, rows=[0], cols=[0], thicks=[2])
        palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
        for d4 in range(8):
            source, _ = compile_target('00dbd492', d4, palette)
            ns = {}
            exec(source, ns)
            result = ns['solve']([], transformed(pair['input'], d4, palette))
            self.assertEqual(result.tolist(), transformed(pair['output'], d4, palette))

    def episode(self, tid, d4=0, palette=None):
        palette = palette or list(range(10))
        task=reference(tid)['teaching_fixture']
        return dict(task_id=tid,episode_id='unit-'+tid,d4_transform=d4,color_permutation=palette,
            train=[{k:transformed(p[k],d4,palette) for k in ('input','output')} for p in task['train']],
            test=[{'input':transformed(p['input'],d4,palette)} for p in task['test']],
            solutions=[transformed(p['output'],d4,palette) for p in task['test']])

    def test_standalone_and_all_augmentations(self):
        for tid in ('0692e18c','00dbd492','00576224','f18ec8cc','b74ca5d1','a6f40cea',
                    '27a28665','9110e3c5','d4469b4b','e12f9a14','f0100645','f560132c','d6542281'):
            for d4 in range(8):
                palette=[3,9,0,7,2,8,1,6,4,5]
                ep=self.episode(tid,d4,palette)
                source,_=compile_target(tid,d4,palette)
                audit_target(tid,source)
                self.assertTrue(verify(source,ep)['all_exact'],(tid,d4))
                self.assertNotIn('arc_agi2',source)

    def test_trace_only_blocks_stay_executable(self):
        source = clean('def transform(grid):\n    if grid:\n        emit(grid)\n    for row in grid:\n        emit(row)\n    return grid\n')
        ns = {}
        exec(source, ns)
        self.assertEqual(ns['transform']([[1, 2]]), [[1, 2]])
        self.assertEqual(ns['transform']([]), [])
        self.assertNotIn('emit', source)

    def test_legend_targets_follow_demonstrations_not_fixed_answers(self):
        for tid in ('27a28665', '9110e3c5', 'd4469b4b'):
            ep = self.episode(tid)
            source, _ = compile_target(tid)
            ns = {}
            exec(source, ns)
            query = ep['test'][0]['input']
            key = ns['legend_key'](query)
            demos = copy.deepcopy(ep['train'])
            for pair in demos:
                if ns['legend_key'](pair['input']) == key:
                    pair['output'] = [[9, 4], [2, 7]]
            self.assertEqual(ns['solve'](demos, query), [[9, 4], [2, 7]])
            missing = [p for p in demos if ns['legend_key'](p['input']) != key]
            with self.assertRaisesRegex(ValueError, 'absent'):
                ns['solve'](missing, query)

    def test_archived_numpy_input_contract_is_preserved(self):
        for tid in ('0d87d2a6', 'c1d99e64'):
            source, _ = compile_target(tid)
            self.assertTrue(verify(source, self.episode(tid))['all_exact'])

    def test_mask_legend_episode_builder_requires_demonstrated_key(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from tasks import task_27a28665 as generator
        from . import build_million as b
        rows = []
        for idx in (1, 2, 3, 6):
            for colour in range(1, 10):
                pair = generator.generate(idx=idx, color=colour)
                canonical = b.canonical_input(pair['input'])
                split = 'validation' if int(canonical[:8],16)%20==0 else 'train'
                rows.append(dict(task_id='27a28665', **pair, seed=idx*10+colour,
                    parameters='{}', generator_mode='default',
                    input_hash=b.digest(pair['input']), canonical_input_hash=canonical,
                    split=split, stratum=b.stratum(pair)))
        with tempfile.TemporaryDirectory() as directory, patch.object(b, 'OUT', Path(directory)):
            file = b.OUT/'pools/27a28665.parquet'
            file.parent.mkdir()
            # One input per legend key cannot teach any held-out key.
            sparse = [r for r in rows if r['seed']%10==1]
            b.pq.write_table(b.pa.Table.from_pylist(sparse), file)
            report = b.make_episodes(('27a28665', {'train':{'3|shrink':2}}))
            self.assertEqual(report['splits']['train']['fresh_episodes'], 0)
            # Repeated masks in different inks supply the needed evidence.
            b.pq.write_table(b.pa.Table.from_pylist(rows), file)
            report = b.make_episodes(('27a28665', {'train':{'3|shrink':2}}))
            self.assertEqual(report['splits']['train']['fresh_episodes'], 2)
            generated = b.pq.read_table(b.OUT/'data/train/27a28665.parquet').to_pylist()
            for episode in generated:
                self.assertEqual(len(set(episode['base_input_hashes'])), 4)
                self.assertTrue(all(int(h[:8],16)%20!=0 for h in episode['canonical_input_hashes']))
                source, _ = compile_target('27a28665',episode['d4_transform'],episode['color_permutation'])
                self.assertTrue(verify(source,episode)['all_exact'])

    def test_query_labels_do_not_construct_program(self):
        ep=self.episode('0692e18c')
        source,_=compile_target(ep['task_id'],ep['d4_transform'],ep['color_permutation'])
        record=make_record(ep)
        altered=copy.deepcopy(ep)
        altered['solutions'][0][0][0]=(altered['solutions'][0][0][0]+1)%10
        source2,_=compile_target(altered['task_id'],altered['d4_transform'],altered['color_permutation'])
        self.assertEqual(source,source2)
        with self.assertRaisesRegex(TargetError,'not exact'):
            make_record(altered)
        self.assertEqual(record['program'],source)
        self.assertIn('```python',record['completion'])
        self.assertIn('```json',record['completion'])
        self.assertEqual(record['episode_id'],ep['episode_id'])
        self.assertEqual(record['mode'],'PROGRAM_AND_GRID')
        self.assertNotIn('solutions',record['prompt'])

    def test_contextual_programs_are_self_contained(self):
        for tid in ('269e22fb','98c475bf'):
            ep=self.episode(tid)
            source,_=compile_target(tid)
            audit_target(tid,source)
            self.assertTrue(verify(source,ep)['all_exact'])

    def test_original_grid_lookup_is_rejected(self):
        tid='0692e18c';a=reference(tid)['canonical']['test'][0]['output']
        with self.assertRaisesRegex(TargetError,'Literal original grid'):
            audit_target(tid,'def solve(demos, grid):\n    return '+repr(a))

    def test_unreviewed_augmentation_cannot_fall_back_to_wrapper(self):
        with self.assertRaisesRegex(TargetError, 'rewrite required'):
            compile_target('cbebaa4b',1)

    def test_no_state_retained_between_pairs(self):
        ep=self.episode('0692e18c')
        source,_=compile_target('0692e18c')
        source+='\n_original_solve=solve\n_calls=0\ndef solve(demos, query):\n    global _calls\n    _calls+=1\n    if _calls!=1: raise RuntimeError("state leaked")\n    return _original_solve(demos,query)\n'
        self.assertTrue(verify(source,ep)['all_exact'])

if __name__=='__main__':unittest.main()

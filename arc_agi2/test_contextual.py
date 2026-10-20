"""Checks that shared-picture episodes are learnable from their demonstrations."""
import copy
import importlib
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from .contextual import solve_shared_picture, verify_shared_picture_episode
from .runtime import reference


class SharedPictureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module('tasks.task_269e22fb')

    def test_canonical_and_contextual_agree(self):
        expected = reference('269e22fb')['canonical']
        self.assertEqual(self.module.validate(), expected)
        self.assertTrue(verify_shared_picture_episode(expected))

    def test_fresh_pictures_without_canonical_access(self):
        pictures = set()
        with patch.object(self.module, '_base', side_effect=AssertionError('canonical lookup')):
            for seed, (height, width) in enumerate([(12, 30), (30, 12), (12, 12), (30, 30)] * 8):
                random.seed(seed)
                episode = self.module.generate_episode(template_height=height, template_width=width)
                self.assertTrue(verify_shared_picture_episode(episode))
                self.assertEqual(len(episode['train']), 3)
                self.assertEqual(len(episode['test']), 1)
                self.assertEqual(len({self.module._equivalence(p['input'])
                                      for p in episode['train'] + episode['test']}), 4)
                output = episode['train'][0]['output']
                self.assertEqual(sorted((len(output), len(output[0]))), sorted((height, width)))
                pictures.add(self.module._equivalence(output))
        self.assertEqual(len(pictures), 32)

    def test_wrong_answer_and_mixed_picture_are_rejected(self):
        random.seed(71001)
        episode = self.module.generate_episode()
        original = solve_shared_picture(episode['train'], episode['test'][0]['input'])
        broken = copy.deepcopy(episode)
        broken['test'][0]['output'][0][0] = (broken['test'][0]['output'][0][0] + 1) % 10
        # Changing the answer has no influence on solving; verification rejects it.
        self.assertEqual(solve_shared_picture(broken['train'], broken['test'][0]['input']), original)
        with self.assertRaisesRegex(ValueError, 'disagreement'):
            verify_shared_picture_episode(broken)
        other = self.module.generate_episode()
        broken['test'] = other['test']
        with self.assertRaises(ValueError):
            verify_shared_picture_episode(broken)

    def test_controls_and_ambiguous_crops(self):
        for kwargs in ({'fg': True}, {'bg': 10}, {'fg': 2, 'bg': 2},
                       {'flip': 1}, {'orientation': 4}, {'width': 31},
                       {'row': -1}, {'template_height': 11},
                       {'template': [[0, 1], [1, 0]]},
                       {'template': self.module._base(), 'template_width': 20}):
            with self.assertRaises(ValueError):
                self.module.generate(**kwargs)
        with self.assertRaises(ValueError):
            self.module.generate(template=self.module._base(), height=1, width=1)

    def test_builder_preserves_context_and_split_through_d4(self):
        from . import build_million as builder
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(builder, 'OUT', Path(tmp)), patch.object(builder, 'POOL_SIZE', 16):
                report = builder.make_pool('269e22fb')
                self.assertEqual(report['pairs'], 16)
                self.assertTrue(report['contextual'])
                rows = pq.read_table(Path(tmp) / 'pools/269e22fb.parquet').to_pylist()
                train = [r for r in rows if r['split'] == 'train']
                self.assertGreaterEqual(len(train), 4)
                for q in rows:
                    pairs = q['context_pairs'] + [q]
                    self.assertEqual(len(pairs), 4)
                    self.assertTrue(verify_shared_picture_episode({'train':pairs[:3], 'test':pairs[3:]}))
                    split_of = lambda digest: 'validation' if int(digest[:8], 16) % 20 == 0 else 'train'
                    self.assertEqual(split_of(q['context_id']), q['split'])
                    self.assertTrue(all(split_of(p['canonical_input_hash']) == q['split'] for p in pairs))
                # Request one fresh episode from each of three available query rows.
                quota = {}
                for row in train[:3]:
                    quota[row['stratum']] = quota.get(row['stratum'], 0) + 1
                result = builder.make_episodes(('269e22fb', {'train': quota}))
                self.assertEqual(result['splits']['train']['fresh_episodes'], 3)
                generated = pq.read_table(Path(tmp) / 'data/train/269e22fb.parquet').to_pylist()
                self.assertEqual(len(generated), 24)
                for row in generated:
                    query = {'input': row['test'][0]['input'], 'output': row['solutions'][0]}
                    self.assertTrue(verify_shared_picture_episode({'train':row['train'], 'test':[query]}))
                    self.assertEqual(json.loads(row['completion']), {'outputs': row['solutions']})
                    self.assertNotIn('context_id', row['prompt'])

    def test_context_and_all_crops_can_enter_validation_together(self):
        from . import build_million as builder
        for seed in range(100):
            four, context_id = builder.picture_episode(self.module, '269e22fb', seed)
            if four[0]['split'] == 'validation':
                self.assertEqual(int(context_id[:8], 16) % 20, 0)
                self.assertTrue(all(int(p['canonical_input_hash'][:8], 16) % 20 == 0
                                    for p in four))
                self.assertTrue(verify_shared_picture_episode({'train':four[:3], 'test':four[3:]}))
                return
        self.fail('No deterministic validation context found in 100 seeds')


class MotifEvidenceTests(unittest.TestCase):
    def test_canonical_requires_demonstrated_marker_templates(self):
        from .motif_context import solve_demonstrated_motifs, MissingMotifEvidence
        episode=reference('98c475bf')['canonical']
        query=episode['test'][0]
        self.assertEqual(solve_demonstrated_motifs(episode['train'],query['input']),query['output'])
        # Only the fourth demonstration shows colour3's template.
        with self.assertRaises(MissingMotifEvidence):
            solve_demonstrated_motifs(episode['train'][:3],query['input'])
        changed=copy.deepcopy(query);changed['output']=[[9]]
        self.assertEqual(solve_demonstrated_motifs(episode['train'],changed['input']),query['output'])
        inconsistent=copy.deepcopy(episode['train'])
        inconsistent[0]['input'][0][2]=0
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            solve_demonstrated_motifs(inconsistent,query['input'])

    def test_motif_controls_and_tight_packing(self):
        m=importlib.import_module('tasks.task_98c475bf')
        from .motif_context import solve_demonstrated_motifs
        demos=reference('98c475bf')['canonical']['train']
        for kw in ({'marker_colours':6},{'markers':5},{'height':21,'num_markers':4}):
            with self.assertRaises(ValueError):m.generate(**kw)
        for seed in range(20):
            random.seed(seed)
            p=m.generate(height=22,num_markers=4)
            self.assertEqual(solve_demonstrated_motifs(demos,p['input']),p['output'])

    def test_episode_builder_rejects_missing_evidence_before_augmentation(self):
        from . import build_million as b
        from .motif_context import solve_demonstrated_motifs
        m=importlib.import_module('tasks.task_98c475bf')
        tid='98c475bf';rows=[];seen=set()
        def add(colour,height):
            for seed in range(1000):
                random.seed(150000+seed+colour*1000+height*100)
                pair=m.generate(height=height,line_color=colour,
                                marker_colours=[3] if height==30 else [7],num_markers=1)
                ch=b.canonical_input(pair['input'])
                if ch in seen or int(ch[:8],16)%20==0:continue
                seen.add(ch)
                row=dict(task_id=tid,**pair,seed=seed,parameters='{}',
                         generator_mode='standalone_constructor',input_hash=b.digest(pair['input']),
                         canonical_input_hash=ch,split='train',stratum=b.stratum(pair))
                rows.append(row);return row
            self.fail('No unique training-split motif input found')
        for _ in range(3):add(6,20)
        query=add(2,30)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'pools').mkdir()
            with patch.object(b,'OUT',root):
                file=root/'pools'/f'{tid}.parquet'
                b.pq.write_table(b.pa.Table.from_pylist(rows),file)
                result=b.make_episodes((tid,{'train':{query['stratum']:1}}))['splits']['train']
                self.assertEqual(result['fresh_episodes'],0)
                self.assertGreater(result['failures']['missing_motif_evidence_attempts'],0)
                add(3,20)
                b.pq.write_table(b.pa.Table.from_pylist(rows),file)
                result=b.make_episodes((tid,{'train':{query['stratum']:1}}))['splits']['train']
                self.assertEqual(result['fresh_episodes'],1)
                generated=b.pq.read_table(root/'data/train'/f'{tid}.parquet').to_pylist()
                native=next(row for row in generated if row['d4_transform']==0)
                # d4=0 fixes geometry, not the episode's colour permutation.
                # This test calls the native verifier, not an SFT program.
                inverse = {v:k for k,v in enumerate(native['color_permutation'])}
                uncolour = lambda g:[[inverse[c] for c in row] for row in g]
                demos = [{k:uncolour(p[k]) for k in ('input','output')}
                         for p in native['train']]
                self.assertEqual(solve_demonstrated_motifs(demos,uncolour(native['test'][0]['input'])),
                                 uncolour(native['solutions'][0]))
                self.assertNotIn('output',native['test'][0])


if __name__ == '__main__':
    unittest.main()

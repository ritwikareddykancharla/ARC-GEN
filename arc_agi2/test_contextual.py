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


if __name__ == '__main__':
    unittest.main()

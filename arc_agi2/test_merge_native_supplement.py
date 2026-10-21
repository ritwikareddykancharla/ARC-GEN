from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from . import merge_native_supplement as m
from . import repair_episode_shortfalls as r
from .test_repair_episode_shortfalls import report, TID, OTHER, REV


class NativeSupplementTests(unittest.TestCase):
    def fixture(self, root):
        snapshot, recovery, supplement, destination = [root / x for x in ('snapshot', 'recovery', 'supplement', 'merged')]
        reports = {TID: report(TID, 2, 1), OTHER: report(OTHER, 4, 1)}
        manifest = {'status': 'complete_with_shortfall', 'seed': 17, 'source_commit': 'old',
                    'target_train_fresh_episodes': 8, 'target_validation_fresh_episodes': 2,
                    'output_format': 'program-grid-png', 'errors': [], **r.totals(reports)}
        allocation = {}
        for split in r.SPLITS:
            amount = 4 if split == 'train' else 1
            allocation[split+'_by_family'] = {t: {'3|same': amount} for t in reports}
            allocation[split] = {'requested': 2*amount, 'desired': {'3|same': 2*amount},
                                  'family_capacity': {t: amount for t in reports}}
        r.write(snapshot/'manifest.json', manifest)
        r.write(recovery/'manifest.json', manifest)
        r.write(recovery/'allocation.json', allocation)
        r.write(recovery/'repair-report.json', {'publishable': True, 'source_dataset_revision': REV,
                                                'accepted_families': [TID], 'delete_files': []})
        for tid, ep in reports.items():
            r.write(snapshot/'episode_reports'/f'{tid}.json', ep)
            if tid == TID:
                r.write(recovery/'episode_reports'/f'{tid}.json', ep)
                for s in ep['splits'].values():
                    for path in s['files']:
                        p = recovery/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'old')
        r.write(snapshot/'pool_reports'/f'{TID}.json', {'sha256': 'old-pool'})
        pool_path = supplement/'pools'/f'{TID}.parquet'
        pool_path.parent.mkdir(parents=True)
        pool_path.write_bytes(b'new verified pool')
        r.write(supplement/'pool_reports'/f'{TID}.json', {
            'task_id': TID, 'complete': True, 'seed': 17, 'source_signature': 'new-source',
            'sha256': r.sha256(pool_path)})
        candidate = report(TID, 4, 1, 'expanded')
        for s in candidate['splits'].values():
            metas = []
            for path in s['files']:
                p = supplement/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(path.encode())
                metas.append({'file': p.name, 'sha256': r.sha256(p), 'episodes': s['episodes']})
            s['shards'] = [{**metas[0], 'viewer_index': metas[1]}]
        r.write(supplement/'episode_reports'/f'{TID}.json', candidate)
        build = {'complete': True, 'source_commit': 'new-source', 'source_dataset_revision': REV,
                 'families': {TID: {'quotas': {'train': {'3|same': 4}, 'validation': {'3|same': 1}},
                                     'prior_pool_sha256': 'old-pool'}}}
        for folder, extension, key in (('pools', 'parquet', 'pool_sha256'),
                                        ('pool_reports', 'json', 'pool_report_sha256'),
                                        ('episode_reports', 'json', 'episode_report_sha256')):
            build['families'][TID][key] = r.sha256(supplement/folder/f'{TID}.{extension}')
        r.write(supplement/'supplement-build.json', build)
        builder = SimpleNamespace(
            pq=SimpleNamespace(read_table=lambda path: SimpleNamespace(to_pylist=lambda: [{'split': 'train'}])),
            repartition_pool=lambda rows, rep: (rows, rep, {'requires_episode_rebuild': False}),
            POLICY={'planned_dataset': {'fresh_episodes_per_family': 4}},
            allocate=lambda reports, split, target, desired: ({}, {'family_capacity': {TID: 4 if split=='train' else 1}}))
        return dict(snapshot=snapshot, recovery=recovery, supplement=supplement, destination=destination, builder=builder)

    def test_merges_counts_paths_and_keeps_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.fixture(Path(tmp))
            old_manifest = r.sha256(args['recovery']/'manifest.json')
            result = m.merge(**args)
            self.assertEqual(result['after_fresh'], 8)
            self.assertFalse(result['published'])
            self.assertEqual(r.sha256(args['recovery']/'manifest.json'), old_manifest)
            dest = args['destination']
            self.assertEqual(r.read(dest/'manifest.json')['status'], 'complete')
            self.assertEqual(r.read(dest/'allocation.json')['train']['allocation_shortfall'], 0)
            self.assertFalse((dest/f'shards/train/{TID}-old.tar').exists())
            self.assertTrue((args['recovery']/f'shards/train/{TID}-old.tar').exists())
            self.assertTrue((dest/f'shards/train/{TID}-expanded.tar').exists())
            merged = {**r.load_reports(args['snapshot']), **r.load_reports(dest)}
            r.verify_source_counts(r.read(dest/'manifest.json'), merged)
            self.assertIn(f'shards/train/{TID}-old.tar', r.read(dest/'repair-report.json')['delete_files'])

    def test_rejects_bad_inputs_before_creating_destination(self):
        for failure in ('hash', 'incomplete', 'revision', 'active', 'split', 'validation_quota', 'regression'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                args = self.fixture(Path(tmp))
                supplement = args['supplement']
                build = r.read(supplement/'supplement-build.json')
                if failure == 'hash':
                    (supplement/f'pools/{TID}.parquet').write_bytes(b'changed')
                elif failure == 'incomplete':
                    build['complete'] = False
                elif failure == 'revision':
                    build['source_dataset_revision'] = 'different'
                elif failure == 'active':
                    manifest = r.read(args['recovery']/'manifest.json')
                    manifest['status'] = 'constructing_episodes'
                    r.write(args['recovery']/'manifest.json', manifest)
                elif failure == 'split':
                    args['builder'].repartition_pool = lambda rows, report: (rows, report, {'requires_episode_rebuild': True})
                elif failure == 'validation_quota':
                    allocation = r.read(args['recovery']/'allocation.json')
                    allocation['validation_by_family'][TID]['3|same'] = 2
                    r.write(args['recovery']/'allocation.json', allocation)
                elif failure == 'regression':
                    ep = r.read(args['recovery']/f'episode_reports/{TID}.json')
                    ep['splits']['train']['fresh_episodes'] = 5
                    r.write(args['recovery']/f'episode_reports/{TID}.json', ep)
                    reports = {**r.load_reports(args['snapshot']), **r.load_reports(args['recovery'])}
                    manifest = r.read(args['recovery']/'manifest.json'); manifest.update(r.totals(reports))
                    r.write(args['recovery']/'manifest.json', manifest)
                r.write(supplement/'supplement-build.json', build)
                with self.assertRaises(ValueError):
                    m.merge(**args)
                self.assertFalse(args['destination'].exists())


if __name__ == '__main__':
    unittest.main()

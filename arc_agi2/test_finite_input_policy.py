"""Tests for the narrow finite-input exception and global split reservation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .augmentation import transformed
from . import finite_input_policy as policy


def canonical_hash(grid):
    """Same published canonical encoding, without importing the live builder."""
    versions = []
    for d4 in range(8):
        a = transformed(grid, d4, list(range(10)))
        lookup, flat = {}, []
        for row in a:
            for colour in row:
                lookup.setdefault(colour, len(lookup))
                flat.append(lookup[colour])
        versions.append(bytes([len(a), len(a[0]), *flat]))
    return hashlib.sha256(min(versions)).hexdigest()


def report(task_id, exact, canonical):
    return {'task_id': task_id, 'train_strata': {'3|same_shape': exact},
            'validation_strata': {}, 'train_canonical': canonical,
            'validation_canonical': 0}


class FiniteInputPolicyTests(unittest.TestCase):
    def test_only_audited_families_and_existing_exception(self):
        self.assertEqual(policy.FINITE_INPUT_TASK_IDS, {
            '0d3d703e', '3979b1a8', '4522001f', '66e6c45b', '833966f4',
            '8b28cd80', '93b581b8', '94414823', 'a85d4709', 'bda2d7a6',
            'ca8de6ea', '27a28665', 'e9afcf9a', 'eb281b96', 'f3e62deb'})
        for tid in policy.FINITE_INPUT_TASK_IDS:
            self.assertEqual(policy.identity_key(tid), 'input_hash')
            self.assertEqual(policy.minimum_class_requirement(tid), 4)
        # Similar-looking low-orbit cases are deliberately NOT blanket admitted.
        self.assertEqual(policy.identity_key('72207abc'), 'canonical_input_hash')

    def test_four_exact_inputs_mandatory_even_with_one_orbit(self):
        from tasks import task_4522001f
        pairs = [task_4522001f.generate(quadrant=q) for q in range(4)]
        exact = {json.dumps(p['input']) for p in pairs}
        orbits = {canonical_hash(p['input']) for p in pairs}
        self.assertEqual(len(exact), 4)
        self.assertEqual(len(orbits), 1)
        self.assertEqual(policy.capacity_basis(report('4522001f', 4, 1), 'train'), 4)
        self.assertEqual(policy.capacity_basis(report('4522001f', 3, 1), 'train'), 0)
        self.assertEqual(policy.capacity_basis(report('27a28665', 3, 1), 'train'), 0)

    def test_capacity_counts_support_not_augmented_or_episode_quota(self):
        self.assertEqual(policy.capacity_basis(report('66e6c45b', 1200, 1), 'train'), 1200)
        self.assertEqual(policy.capacity_basis(report('72207abc', 1152, 4), 'train'), 4)
        self.assertEqual(policy.capacity_basis(report('ordinary', 1200, 3), 'train'), 0)

    def test_global_reservation_matches_actual_833_and_feca_fixtures(self):
        base = Path(__file__).parent / 'references'
        a = json.loads((base / '833966f4.json').read_text())['canonical']['train'][0]['input']
        b = json.loads((base / 'feca6190.json').read_text())['canonical']['test'][0]['input']
        self.assertEqual(canonical_hash(a), canonical_hash(b))
        self.assertEqual({canonical_hash(a)}, policy.GLOBAL_TRAIN_ORBITS)
        self.assertEqual(int(canonical_hash(a)[:8], 16) % 20, 0)
        for grid in (a, b, transformed(a, 1, list(reversed(range(10))))):
            self.assertEqual(policy.input_split(canonical_hash(grid)), 'train')

    def test_other_hashes_preserve_original_global_split(self):
        hashes = [hashlib.sha256(str(i).encode()).hexdigest() for i in range(1000)]
        for h in hashes:
            self.assertEqual(policy.input_split(h),
                             'validation' if int(h[:8], 16) % 20 == 0 else 'train')
        self.assertEqual(len(policy.GLOBAL_TRAIN_ORBITS), 1)

    def test_zigzag_finite_family_keeps_its_two_validation_orbits(self):
        from tasks import task_eb281b96
        by_split={'train':set(),'validation':set()}
        for stretch in range(1,5):
            for colour in range(1,10):
                h=canonical_hash(task_eb281b96.generate(stretch=stretch,color=colour)['input'])
                self.assertNotIn(h,policy.GLOBAL_TRAIN_ORBITS)
                by_split[policy.input_split(h)].add(h)
        self.assertEqual({s:len(v) for s,v in by_split.items()}, {'train':2,'validation':2})
        r={'task_id':'eb281b96','train_canonical':2,'validation_canonical':2,
           'train_strata':{'17|expand':18},'validation_strata':{'17|expand':18}}
        self.assertEqual(policy.capacity_basis(r,'train'),18)
        self.assertEqual(policy.capacity_basis(r,'validation'),18)

    def test_stale_all_validation_report_not_silently_recounted(self):
        r = report('833966f4', 0, 0)
        r.update(validation_strata={'5|same_shape': 1200}, validation_canonical=1)
        self.assertEqual(policy.capacity_basis(r, 'train'), 0)
        # Integrator must rebuild these counts before making ANY episodes.
        self.assertEqual(policy.capacity_basis(r, 'validation'), 1200)

    def test_provenance_matches_native_sources_and_is_read_only(self):
        root = Path(__file__).resolve().parents[1]
        for tid, info in policy.FAMILY_PROVENANCE.items():
            self.assertEqual(hashlib.sha256((root / info['native_source']).read_bytes()).hexdigest(),
                             info['native_source_sha256'], tid)
            self.assertTrue(info['mechanism'])
        with self.assertRaises(TypeError):
            policy.FAMILY_PROVENANCE['833966f4']['mechanism'] = 'changed'
        self.assertEqual(len(policy.POLICY_SIGNATURE), 64)

    def test_invalid_metadata_fails_closed(self):
        for h in ('', '0' * 63, 'g' * 64, None):
            with self.assertRaises(ValueError):
                policy.input_split(h)
        for n in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                policy.capacity_basis(report('4522001f', n, 1), 'train')
        with self.assertRaises(ValueError):
            policy.capacity_basis(report('4522001f', 4, 1), 'test')
        with self.assertRaises(KeyError):
            policy.capacity_basis({'task_id': '4522001f'}, 'train')


class BuilderIntegrationTests(unittest.TestCase):
    @staticmethod
    def row(tid, grid, output=None, split=None):
        from . import build_million as b
        pair={'input':grid,'output':grid if output is None else output}
        ch=b.canonical_input(grid)
        return dict(pair,task_id=tid,input_hash=b.digest(grid),canonical_input_hash=ch,
                    split=policy.input_split(ch) if split is None else split,
                    stratum=b.stratum(pair),seed=1,parameters='{}',generator_mode='default')

    def test_repartition_recounts_both_families_without_mutating_inputs(self):
        from . import build_million as b
        for tid in ('833966f4','feca6190'):
            rows=[self.row(tid, [[c] for c in colours], split='validation')
                  for colours in ([0,1,2,3,4],[1,2,3,4,5],[2,3,4,5,6],[3,4,5,6,7])]
            before=json.dumps(rows)
            old=dict(task_id=tid,pairs=4,contextual=False,requested_pool_size=4,
                     source_signature='old-source',sha256='old-file')
            revised,metadata,migration=b.repartition_pool(rows,old)
            self.assertEqual(json.dumps(rows),before)
            self.assertEqual({p['split'] for p in revised},{'train'})
            self.assertEqual(metadata['train_canonical'],1)
            self.assertEqual(metadata['validation_canonical'],0)
            self.assertEqual(sum(metadata['train_strata'].values()),4)
            self.assertEqual(metadata['validation_strata'],{})
            self.assertEqual(len(migration['changed_inputs']),4)
            self.assertTrue(migration['requires_episode_rebuild'])
            self.assertEqual(migration['original_source_signature'],'old-source')
            self.assertNotIn('source_signature',metadata)
            self.assertNotIn('sha256',metadata)

    def test_repartition_drops_whole_inconsistent_stored_context(self):
        from . import build_million as b
        grids=[[[int(mask & (1 << (r*3+c)) > 0) for c in range(3)] for r in range(3)]
               for mask in range(512)]
        stays_validation=next(g for g in grids if policy.input_split(b.canonical_input(g))=='validation')
        q=self.row('context',[[0],[1],[2],[3],[4]],split='validation')
        q['context_pairs']=[self.row('context',stays_validation)]
        revised,metadata,migration=b.repartition_pool([q],dict(task_id='context',contextual=True,requested_pool_size=1))
        self.assertEqual(revised,[])
        self.assertFalse(metadata['complete'])
        self.assertEqual(metadata['validation_context_episodes'],0)
        self.assertEqual(metadata['pool_shortfall'],1)
        self.assertEqual(len(migration['dropped_stored_contexts']),1)

    def test_repartition_rejects_corrupt_hashes_and_duplicate_queries(self):
        from . import build_million as b
        row=self.row('ordinary',[[1,2],[3,4]])
        with self.assertRaises(ValueError):b.repartition_pool([row,row],{'task_id':'ordinary'})
        row['canonical_input_hash']='0'*64
        with self.assertRaises(ValueError):b.repartition_pool([row],{'task_id':'ordinary'})

    def test_real_allocator_uses_exact_support_only_for_allowlist(self):
        from . import build_million as b
        reports=[dict(report('4522001f',4,1),contextual=False),
                 dict(report('ordinary',1200,1),contextual=False)]
        allocation,summary=b.allocate(reports,'train',2000,{'3|same_shape':1})
        self.assertEqual(sum(allocation['4522001f'].values()),4)
        self.assertNotIn('ordinary',allocation)
        self.assertEqual(summary['family_capacity_shortfall']['4522001f'],996)

    def test_real_episode_builder_uses_four_exact_inputs_and_keeps_gate(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from tasks import task_4522001f
        from . import build_million as b
        rows=[]
        for quadrant in range(4):
            p=task_4522001f.generate(quadrant=quadrant)
            rows.append(self.row('4522001f',p['input'],p['output']))
        split=rows[0]['split']
        with tempfile.TemporaryDirectory() as folder, patch.object(b,'OUT',Path(folder)), patch.object(b,'OUTPUT_FORMAT','legacy-grid-parquet'):
            pool=Path(folder)/'pools'/'4522001f.parquet';pool.parent.mkdir()
            pq.write_table(pa.Table.from_pylist(rows),pool)
            with patch.object(b,'require_colour_evidence',wraps=b.require_colour_evidence) as gate:
                result=b.make_episodes(('4522001f',{split:{rows[0]['stratum']:4}}))
            self.assertGreater(gate.call_count,0)
            self.assertEqual(result['splits'][split]['fresh_episodes'],4)
            self.assertEqual(result['splits'][split]['max_query_reuse_in_fresh_episodes'],1)
            stored=pq.read_table(Path(folder)/'data'/split/'4522001f.parquet').to_pylist()
            self.assertTrue(all(len(set(r['base_input_hashes']))==4 for r in stored))
            self.assertTrue(all(len(set(r['canonical_input_hashes']))==1 for r in stored))
            self.assertTrue(all(r['within_episode_input_identity']=='input_hash' for r in stored))

    def test_episode_builder_rejects_stale_reserved_split(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from . import build_million as b
        row=self.row('833966f4',[[0],[1],[2],[3],[4]],split='validation')
        with tempfile.TemporaryDirectory() as folder, patch.object(b,'OUT',Path(folder)):
            pool=Path(folder)/'pools'/'833966f4.parquet';pool.parent.mkdir()
            pq.write_table(pa.Table.from_pylist([row]),pool)
            with self.assertRaisesRegex(ValueError,'globally repartition'):
                b.make_episodes(('833966f4',{'validation':{'5|same_shape':1}}))

    def test_policy_signature_invalidates_pool_cache(self):
        from . import build_million as b
        original=b.pool_signature('4522001f',[])
        with patch.object(b,'FINITE_INPUT_POLICY_SIGNATURE','changed'):
            self.assertNotEqual(original,b.pool_signature('4522001f',[]))


if __name__ == '__main__':
    unittest.main()

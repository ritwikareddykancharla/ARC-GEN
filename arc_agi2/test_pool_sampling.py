"""Focused tests for bounded sampling and reproducible retries."""
import copy
import random
import shutil
import unittest
from unittest.mock import patch
import numpy as np
from . import pool_sampling as sampling

class SamplingTests(unittest.TestCase):
    def test_same_seed_retry_and_caller_rng_restored(self):
        random.seed(918); np.random.seed(919)
        py_before, np_before = random.getstate(), np.random.get_state()
        draws=[]; limits=[]
        def fn():
            draws.append((random.random(), float(np.random.random())))
            if len(draws)==1: raise TimeoutError('simulated slow native draw')
            return {'input':[[1]],'output':[[2]]}
        def invoke(fn, seconds, **kw):
            limits.append(seconds)
            return fn(**kw)
        with patch.object(sampling,'call',side_effect=invoke):
            pair,meta=sampling.sample_native('1b8318e3',fn,123)
        self.assertEqual(draws[0],draws[1]); self.assertEqual(limits,[5.,30.])
        self.assertEqual(pair['output'],[[2]])
        self.assertEqual([a['status'] for a in meta['attempts']],['timeout','success'])
        self.assertEqual(random.getstate(),py_before)
        now=np.random.get_state()
        self.assertEqual(now[0],np_before[0]);np.testing.assert_array_equal(now[1],np_before[1]);self.assertEqual(now[2:],np_before[2:])

    def test_known_docking_long_tail_has_bounded_final_tier(self):
        self.assertEqual(sampling.timeout_limits('1b8318e3'), (5., 30., 300.))
        self.assertEqual(sampling.timeout_limits('plain'), (5.,))

    def test_final_timeout_preserves_seed_and_attempt_metadata(self):
        def fn():raise TimeoutError('still slow')
        with patch.object(sampling,'call',side_effect=lambda fn,seconds,**kw:fn(**kw)):
            with self.assertRaises(sampling.SamplerTimeout) as ctx:
                sampling.sample_native('bd14c3bf',fn,987)
        self.assertEqual(ctx.exception.metadata['seed'],987)
        self.assertEqual([a['limit_seconds'] for a in ctx.exception.metadata['attempts']],[5.,30.])
        self.assertTrue(all(a['status']=='timeout' for a in ctx.exception.metadata['attempts']))

    def test_output_preserved_and_non_timeout_errors_not_retried(self):
        expected={'input':[[1]],'output':[[9]]}
        with patch.object(sampling,'call',return_value=expected) as call:
            result,meta=sampling.sample_native('plain',lambda:None,1)
        self.assertIs(result,expected);self.assertEqual(call.call_count,1)
        with patch.object(sampling,'call',side_effect=ValueError('invalid parameters')) as call:
            with self.assertRaises(ValueError):sampling.sample_native('bd14c3bf',lambda:None,1)
        self.assertEqual(call.call_count,1)

    def test_compiler_fallback_is_explicit(self):
        with patch.object(sampling,'_compiled_985',side_effect=sampling.SamplingSetupError('no compiler')),patch.object(sampling,'call',return_value={'input':[[0]],'output':[[0]]}):
            _,meta=sampling.sample_native('985ae207',lambda:None,4)
        self.assertEqual(meta['mode'],'native');self.assertEqual(meta['compiled_fallback_reason'],'no compiler')
        self.assertTrue(meta['native_seed_equivalent'])

    def test_explicit_parameters_never_use_compiled_sampler(self):
        with patch.object(sampling,'_compiled_985') as compiled,patch.object(sampling,'call',return_value={'input':[[0]],'output':[[0]]}) as call:
            _,meta=sampling.sample_native('985ae207',lambda **kw:None,4,{'size':20})
        compiled.assert_not_called();self.assertEqual(call.call_args.kwargs['size'],20)
        self.assertEqual(meta['parameters'],{'size':20})

    @unittest.skipUnless(shutil.which('c++') or shutil.which('g++'),'C++ compiler absent')
    def test_audited_compiled_sampler_reproducible_native_rendering(self):
        from tasks import task_985ae207 as native
        first,meta=sampling.sample_native('985ae207',native.generate,10910000)
        second,again=sampling.sample_native('985ae207',native.generate,10910000)
        self.assertEqual(first,second)
        self.assertEqual(meta['mode'],'compiled_parameter_sampler')
        self.assertFalse(meta['native_seed_equivalent'])
        self.assertEqual(meta['sampler_source_sha256'],sampling.SAMPLER_985_SHA256)
        self.assertEqual(meta['derived_seed'],again['derived_seed'])
        self.assertGreater(meta['proposal_attempts'],0)
        self.assertEqual(first,native.generate(**meta['explicit_parameters']))
        self.assertIsNotNone(first['input']);self.assertIsNotNone(first['output'])


class PoolIntegrationTests(unittest.TestCase):
    def test_complete_raw_pool_includes_all_ambiguous_draws_and_hash_guard(self):
        from tasks import task_1b8318e3 as native
        records,meta=sampling.load_native_seed_pool('1b8318e3',native.generate)
        self.assertEqual([r['index'] for r in records],list(range(1150)))
        self.assertEqual(sum(r['status']=='ambiguous' for r in records),33)
        self.assertFalse(meta['fresh_draws_this_job'])
        with patch.object(sampling,'RAW_1B_POOL_SHA256','bad'):
            with self.assertRaises(sampling.SamplingSetupError):sampling.load_native_seed_pool('1b8318e3',native.generate)

    def test_builder_imports_full_stream_without_fresh_sampling(self):
        import tempfile,json
        from pathlib import Path
        from . import build_million as builder
        with tempfile.TemporaryDirectory() as directory,patch.object(builder,'OUT',Path(directory)),patch.object(builder,'POOL_SIZE',1150),patch.object(builder,'sample_native',side_effect=SystemExit('Unexpected fresh draw')) as sampler:
            report=builder.make_pool('1b8318e3')
            self.assertEqual(report['pairs'],1150)
            self.assertEqual(report['archived_records_consumed'],1150)
            self.assertEqual(report['archived_status_counts_consumed'],{'unique':1117,'ambiguous':33})
            self.assertEqual(report['termination_reason'],'requested_pool_reached')
            self.assertTrue(report['quota_complete']);sampler.assert_not_called()
            rows=builder.pq.read_table(Path(directory)/'pools/1b8318e3.parquet').to_pylist()
            statuses=[json.loads(r['parameters'])['sampling']['archived_status'] for r in rows]
            self.assertEqual(statuses.count('ambiguous'),33)
            self.assertEqual(builder.make_pool('1b8318e3')['sha256'],report['sha256'])

    def test_family_budget_invalidates_cache_signature(self):
        from . import build_million as builder
        with patch.dict('os.environ',{'ARCGEN_FAMILY_SECONDS_1B8318E3':'3600'}):
            a=builder.pool_signature('1b8318e3',[])
        with patch.dict('os.environ',{'ARCGEN_FAMILY_SECONDS_1B8318E3':'3601'}):
            b=builder.pool_signature('1b8318e3',[])
        self.assertNotEqual(a,b)

    def test_builder_exhausted_sampler_reports_attempts_and_shortfall(self):
        import tempfile
        from pathlib import Path
        from . import build_million as builder
        meta={'task_id':'bd14c3bf','seed':999,'mode':'native','attempts':[{'limit_seconds':5,'status':'timeout'},{'limit_seconds':30,'status':'timeout'}]}
        with tempfile.TemporaryDirectory() as directory,patch.object(builder,'OUT',Path(directory)),patch.object(builder,'POOL_SIZE',1),patch.object(builder,'sample_native',side_effect=lambda *a,**k:(_ for _ in ()).throw(sampling.SamplerTimeout(copy.deepcopy(meta)))):
            report=builder.make_pool('bd14c3bf')
        self.assertFalse(report['complete']);self.assertEqual(report['pool_shortfall'],1)
        self.assertEqual(report['termination_reason'],'draw_attempt_limit')
        self.assertEqual(report['sampling_timeout_attempts'],80)
        self.assertEqual(report['rejections']['sampler_timeout_exhausted'],40)

if __name__=='__main__':unittest.main()

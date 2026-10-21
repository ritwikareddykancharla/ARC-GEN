"""Quota invariants on the real allocator, without Hub/storage dependencies."""
import ast
from collections import Counter
import hashlib
from pathlib import Path
import unittest


def allocator(ceiling=1000):
    source=Path(__file__).with_name('build_million.py').read_text()
    function=next(n for n in ast.parse(source).body
                  if isinstance(n,ast.FunctionDef) and n.name=='allocate')
    namespace={'Counter':Counter,
               'POLICY':{'planned_dataset':{'fresh_episodes_per_family':ceiling}},
               'seed':lambda *x:int(hashlib.sha256(repr(x).encode()).hexdigest(),16)}
    exec(compile(ast.Module(body=[function],type_ignores=[]),'<actual allocate>','exec'),namespace)
    return namespace['allocate']


def report(tid,strata,canonical=None,contextual=False):
    return {'task_id':tid,'train_canonical':sum(strata.values()) if canonical is None else canonical,
            'train_strata':strata,'contextual':contextual,
            'train_context_episodes':sum(strata.values()) if contextual else 0}


class AllocationTests(unittest.TestCase):
    def test_all_rich_families_get_1000_despite_unavailable_target_sizes(self):
        rows=[report('a',{'3|expand':600}),report('b',{'3|expand':600})]
        allocation,stats=allocator()(rows,'train',2000,{'3|expand':1,'30|same':99})
        self.assertEqual({t:sum(q.values()) for t,q in allocation.items()},{'a':1000,'b':1000})
        self.assertEqual(stats['allocated'],2000)
        self.assertEqual(stats['allocation_shortfall'],0)
        self.assertEqual(stats['quota_recovered_outside_histogram'],1980)
        self.assertEqual(stats['shortfall_by_stratum'],{'30|same':1980})
        self.assertEqual(stats['histogram_surplus_by_stratum'],{'3|expand':1980})

    def test_family_absent_from_original_histogram_is_not_dropped(self):
        rows=[report('large',{'30|same':600}),report('small',{'7|shrink':600})]
        allocation,stats=allocator()(rows,'train',2000,{'30|same':1})
        self.assertEqual(allocation,{'large':{'30|same':1000},'small':{'7|shrink':1000}})
        self.assertEqual(stats['allocation_shortfall'],0)

    def test_feasible_histogram_is_preserved(self):
        rows=[report('a',{'5|same':600}),report('b',{'30|same':600})]
        allocation,stats=allocator()(rows,'train',2000,{'5|same':1,'30|same':1})
        self.assertEqual(stats['actual'],stats['desired'])
        self.assertEqual(stats['quota_recovered_outside_histogram'],0)
        self.assertEqual(sum(sum(v.values()) for v in allocation.values()),2000)

    def test_limited_diversity_remains_explicit_and_cannot_pad_rich_family(self):
        rows=[report('tiny',{'3|same':5}),report('rich',{'30|same':2000})]
        allocation,stats=allocator()(rows,'train',2000,{'20|same':1})
        self.assertEqual(sum(allocation['tiny'].values()),20)
        self.assertEqual(sum(allocation['rich'].values()),1000)
        self.assertEqual(stats['allocation_shortfall'],980)
        self.assertEqual(stats['family_capacity_shortfall'],{'tiny':980})

    def test_canonical_classes_gate_context_not_total_episode_budget(self):
        rows=[report('aliased',{'3|same':600,'9|expand':600},canonical=7)]
        allocation,stats=allocator()(rows,'train',1000,{'30|same':1})
        self.assertEqual(sum(allocation['aliased'].values()),1000)
        self.assertEqual(stats['allocation_shortfall'],0)

    def test_finite_query_reuse_exception_remains_one(self):
        allocation,stats=allocator()([report('4522001f',{'3|same':4},canonical=1)],'train',1000,{})
        self.assertEqual(allocation,{'4522001f':{'3|same':4}})
        self.assertEqual(stats['allocation_shortfall'],996)

    def test_ordinary_budget_matches_existing_four_query_limit(self):
        allocation,stats=allocator()([report('017c7c7b',{'6|expand':254},canonical=41)],'train',1000,{})
        self.assertEqual(allocation,{'017c7c7b':{'6|expand':1000}})
        allocation,stats=allocator()([report('small',{'6|expand':200},canonical=41)],'train',1000,{})
        self.assertEqual(sum(allocation['small'].values()),800)
        self.assertFalse(stats['capacity_is_verified_episode_count'])

    def test_three_canonical_classes_remain_ineligible_with_many_exact_inputs(self):
        allocation,stats=allocator()([report('ordinary',{'6|expand':1200},canonical=3)],'train',1000,{})
        self.assertEqual(allocation,{})
        self.assertEqual(stats['allocation_shortfall'],1000)

    def test_contextual_episode_support_is_not_reused_to_fill_quota(self):
        rows=[report('context',{'3|same':4,'30|same':600},contextual=True)]
        allocation,stats=allocator()(rows,'train',1000,{'3|same':1})
        self.assertEqual(allocation,{'context':{'3|same':4,'30|same':600}})
        self.assertEqual(stats['allocation_shortfall'],396)

    def test_small_global_budget_not_exceeded_and_recovery_balanced(self):
        rows=[report(t,{'3|same':600}) for t in ['a','b','c']]
        allocation,stats=allocator()(rows,'train',20,{'30|same':1})
        totals=[sum(q.values()) for q in allocation.values()]
        self.assertEqual(sum(totals),20)
        self.assertLessEqual(max(totals)-min(totals),1)
        self.assertEqual(stats['allocation_shortfall'],0)

    def test_input_order_is_irrelevant(self):
        rows=[report('a',{'3|same':600,'10|expand':20}),report('b',{'10|expand':600})]
        forward=allocator()(rows,'train',1500,{'30|same':1,'3|same':1})
        reverse=allocator()(rows[::-1],'train',1500,{'30|same':1,'3|same':1})
        self.assertEqual(forward,reverse)

    def test_no_histogram_can_still_allocate_only_real_support(self):
        allocation,stats=allocator()([report('a',{'9|same':600})],'train',1000,{})
        self.assertEqual(allocation,{'a':{'9|same':1000}})
        self.assertEqual(stats['allocation_shortfall'],0)

    def test_ineligible_family_is_reported_not_fabricated(self):
        allocation,stats=allocator()([report('a',{'3|same':3})],'train',1000,{'3|same':1})
        self.assertEqual(allocation,{})
        self.assertEqual(stats['family_capacity_shortfall'],{'a':1000})
        self.assertEqual(stats['allocation_shortfall'],1000)

    def test_zero_target_and_invalid_negative_counts(self):
        rows=[report('a',{'3|same':600})]
        self.assertEqual(allocator()(rows,'train',0,{'3|same':1})[0],{})
        with self.assertRaises(ValueError):allocator()(rows,'train',-1,{'3|same':1})
        with self.assertRaises(ValueError):allocator()(rows,'train',1,{'3|same':-1})


if __name__=='__main__':unittest.main()

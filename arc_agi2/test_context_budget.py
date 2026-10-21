from collections import Counter
from itertools import combinations
import random
import unittest

from .context_budget import bounds, reuse_limits, VERSION


class ContextBudgetTests(unittest.TestCase):
    def test_bounds_equal_exhaustive_distinct_query_context_enumeration(self):
        rng = random.Random(37)
        for n in range(1, 13):
            for _ in range(10):
                rows = [{'input_hash': str(i), 'canonical_input_hash': str(rng.randrange(6)),
                         'stratum': str(rng.randrange(3))} for i in range(n)]
                for identity in ('input_hash', 'canonical_input_hash'):
                    expected = Counter()
                    for q in rows:
                        eligible = [p for p in rows if p[identity] != q[identity]]
                        expected[q['stratum']] += sum(len({p[identity] for p in ds}) == 3
                                                      for ds in combinations(eligible, 3))
                    self.assertEqual(bounds(rows, identity), dict(expected))

    def test_four_finite_inputs_yield_four_episodes_not_order_permutations(self):
        rows = [{'input_hash': str(i), 'stratum': '3|same'} for i in range(4)]
        self.assertEqual(bounds(rows, 'input_hash'), {'3|same': 4})
        self.assertEqual(reuse_limits(4, 4, finite=True), (2, 32))

    def test_twenty_four_inputs_have_more_than_twenty_four_contexts(self):
        rows = [{'input_hash': str(i), 'stratum': '3|same'} for i in range(24)]
        self.assertEqual(bounds(rows, 'input_hash'), {'3|same': 42504})
        q, p = reuse_limits(1000, 24, finite=True)
        self.assertGreaterEqual(q*24, 1000)
        self.assertGreaterEqual(p*24, 4000)

    def test_stored_contexts_do_not_gain_combinatorial_recombinations(self):
        rows = [{'input_hash': str(i), 'stratum': '3|same'} for i in range(24)]
        self.assertEqual(bounds(rows, 'input_hash', True), {'3|same': 24})
        self.assertEqual(reuse_limits(1000, 24, stored_context=True), (1, 32))

    def test_duplicate_exact_queries_are_rejected(self):
        with self.assertRaises(ValueError):
            bounds([{'input_hash': 'same'}, {'input_hash': 'same'}], 'input_hash')

    def test_allocator_uses_audited_context_bound_and_keeps_ceiling(self):
        from . import build_million as b
        report = {'task_id': '4522001f', 'complete': True,
                  'train_strata': {'3|same': 4}, 'train_canonical': 1,
                  'context_budget_version': VERSION,
                  'train_distinct_context_upper_by_stratum': {'3|same': 4}}
        allocation, audit = b.allocate([report], 'train', 1000, {'3|same': 1000})
        self.assertEqual(sum(allocation['4522001f'].values()), 4)
        self.assertEqual(audit['capacity_policy'], VERSION)
        self.assertFalse(audit['capacity_is_verified_episode_count'])
        report.update(task_id='0d3d703e', train_strata={'3|same': 24},
                      train_distinct_context_upper_by_stratum={'3|same': 42504})
        allocation, _ = b.allocate([report], 'train', 1000, {'3|same': 1000})
        self.assertEqual(sum(allocation['0d3d703e'].values()), 1000)


if __name__ == '__main__':
    unittest.main()

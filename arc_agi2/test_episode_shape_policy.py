import random
import unittest
from .episode_shape_policy import VERSION, profile_from_task, select_demonstrations


def pair(height, width, colour=0):
    return {'input': [[colour]*width for _ in range(height)]}


def policy(mode, relation):
    return {'version': VERSION, 'patterns': [
        {'demo_input_shapes': mode, 'query_input_shape': relation}]}


class ShapePolicyTests(unittest.TestCase):
    def test_profile_preserves_query_pattern_frequency_without_outputs(self):
        task={'train':[pair(3,4),pair(3,4)],
              'test':[pair(3,4),pair(3,4),pair(4,3)]}
        result=profile_from_task(task)
        self.assertEqual(result['patterns'],[
            {'demo_input_shapes':'uniform','query_input_shape':'seen'},
            {'demo_input_shapes':'uniform','query_input_shape':'seen'},
            {'demo_input_shapes':'uniform','query_input_shape':'novel'}])

    def test_all_four_patterns_when_supported(self):
        candidates=[pair(h,w,c) for h,w in [(3,4),(4,3),(5,5)] for c in range(4)]
        for mode in ('uniform','mixed'):
            for relation in ('seen','novel'):
                for seed in range(20):
                    demos,report=select_demonstrations(candidates,pair(3,4)['input'],random.Random(seed),policy(mode,relation))
                    self.assertTrue(report['matched'],report)
                    self.assertIsNone(report['fallback'])
                    self.assertEqual(len({id(p) for p in demos}),3)
                    self.assertTrue(all(any(p is candidate for candidate in candidates) for p in demos))

    def test_uniform_support_shortage_reports_fallback(self):
        candidates=[pair(3,4),pair(4,3),pair(5,5)]
        demos,report=select_demonstrations(candidates,pair(3,4)['input'],random.Random(2),policy('uniform','seen'))
        self.assertFalse(report['matched'])
        self.assertEqual(report['fallback'],'requested_shape_pattern_unavailable_in_candidate_pool')
        self.assertEqual(len(demos),3)

    def test_novel_pattern_does_not_select_query_shape_when_feasible(self):
        candidates=[pair(3,4,c) for c in range(6)]+[pair(4,3,c) for c in range(2)]+[pair(5,5)]
        demos,report=select_demonstrations(candidates,pair(3,4)['input'],random.Random(4),policy('mixed','novel'))
        self.assertTrue(report['matched'])
        self.assertTrue(all((len(p['input']),len(p['input'][0]))!=(3,4) for p in demos))

    def test_insufficient_candidates_are_not_duplicated(self):
        demos,report=select_demonstrations([pair(3,3),pair(4,4)],pair(3,3)['input'],random.Random(1),policy('mixed','seen'))
        self.assertIsNone(demos)
        self.assertEqual(report['fallback'],'insufficient_candidate_demonstrations')

    def test_selected_input_sequence_is_independent_of_labels(self):
        candidates=[pair(h,h,c) for h in (3,4,5) for c in range(4)]
        clean,first=select_demonstrations(candidates,pair(3,3)['input'],random.Random(8),policy('mixed','seen'))
        poisoned=[dict(p,output=[[9]*30 for _ in range(30)]) for p in candidates]
        changed,second=select_demonstrations(poisoned,pair(3,3)['input'],random.Random(8),policy('mixed','seen'))
        self.assertEqual([p['input'] for p in clean],[p['input'] for p in changed])
        self.assertEqual(first,second)

    def test_reproducible_and_does_not_mutate_pool(self):
        candidates=[pair(h,h,c) for h in (3,4,5) for c in range(4)]
        before=[id(x) for x in candidates]
        a=select_demonstrations(candidates,pair(3,3)['input'],random.Random(8),policy('mixed','seen'))
        b=select_demonstrations(candidates,pair(3,3)['input'],random.Random(8),policy('mixed','seen'))
        self.assertEqual(a,b)
        self.assertEqual(before,[id(x) for x in candidates])

    def test_mixed_reference_profile_is_not_coerced_to_uniform(self):
        p=profile_from_task({'train':[pair(3,4),pair(5,6)],'test':[pair(7,8)]})
        self.assertEqual(p['patterns'],[{'demo_input_shapes':'mixed','query_input_shape':'novel'}])

    def test_invalid_profile_is_not_silently_ignored(self):
        with self.assertRaises(ValueError):profile_from_task({'train':[],'test':[]})
        with self.assertRaises(ValueError):select_demonstrations([],[[0]],random.Random(1),{'patterns':[]})


if __name__=='__main__':unittest.main()

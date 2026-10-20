"""Keep equal counts when demos teach their ordering; do not rely on dict order."""
import random
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.count_sort_evidence import count_sort_variants
from tasks import task_bd283c4a as counts


class CountSortEvidenceTests(unittest.TestCase):
    palette = [3,9,0,7,2,8,1,6,4,5]

    def pair(self,numbers,seed):
        values = [v for v,n in enumerate(numbers,1) for _ in range(n)]
        random.Random(seed).shuffle(values)
        return counts.generate(colors=values)

    def test_tied_query_needs_tied_demonstration(self):
        data = counts.validate()
        strong = self.pair([25]*4,5)
        query = self.pair([60,20,10,10],17)
        for d4 in range(8):
            ds = apply_episode(data['train'],d4,self.palette)
            ss = apply_episode([strong],d4,self.palette)
            q,untied = apply_episode([query,data['test'][0]],d4,self.palette)
            for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[0]])):
                with self.subTest(d4=d4),self.assertRaises(MissingColourEvidence):
                    require_colour_evidence('bd283c4a',ds,[payload],self.palette,d4)
            require_colour_evidence('bd283c4a',ds+ss,[{'input':q['input']}],self.palette,d4)
            require_colour_evidence('bd283c4a',ds,[{'input':untied['input']}],self.palette,d4)

    def test_native_rule_and_candidate_sets_are_d4_closed(self):
        for numbers in ([25]*4,[60,20,10,10],[49,31,15,5],[100]):
            p = self.pair(numbers,13)
            original = count_sort_variants(p['input'])
            self.assertEqual(original[48],p['output'])
            for d4 in range(8):
                pair = apply_episode([p],d4,self.palette)[0]
                observed = {tuple(map(tuple,v)) for v in count_sort_variants(pair['input'])}
                expected = {tuple(map(tuple,apply_episode([dict(input=p['input'],output=v)],d4,self.palette)[0]['output'])) for v in original}
                self.assertEqual(observed,expected)

    def test_uniform_demos_cannot_teach_fill_direction(self):
        weak = self.pair([100],0)
        query = self.pair([60,20,15,5],0)
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('bd283c4a',[weak],[{'input':query['input']}])
        require_colour_evidence('bd283c4a',counts.validate()['train'],[{'input':query['input']}])

    def test_corrupt_demo_is_not_accepted(self):
        p = self.pair([60,20,15,5],0)
        wrong = dict(input=p['input'],output=[[9]*10 for _ in range(10)])
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('bd283c4a',[wrong],[{'input':p['input']}])


if __name__ == '__main__': unittest.main()

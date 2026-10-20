"""Teach mirror axis and colour role; retain minority-colour foregrounds."""
import random
import unittest
from collections import Counter
from arc_agi2.augmentation import apply_episode,transformed
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.central_mirror_evidence import central_mirror_variants
from arc_agi2.direct_factories.task_c35c1b4c import build_program
from tasks import task_c35c1b4c as task


class CentralMirrorTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def setUp(self):
        self.data=task.validate()
        ns={};exec(build_program(0,list(range(10))),ns);self.solve=ns['solve']

    def test_uninformative_context_rejected_then_informative_demos_recover(self):
        random.seed(1);q=task.generate()
        weak=dict(input=[[7]*10 for _ in range(10)],output=[[7]*10 for _ in range(10)])
        for d4 in range(8):
            ds=apply_episode([weak],d4,self.palette)
            strong=apply_episode(self.data['train'],d4,self.palette)
            query=apply_episode([q],d4,self.palette)[0]
            for item in ({'input':query['input']},query,dict(input=query['input'],output=[[99]])):
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence('c35c1b4c',ds,[item],self.palette,d4)
                require_colour_evidence('c35c1b4c',strong,[item],self.palette,d4)
            with self.assertRaisesRegex(ValueError,'resolve'):
                self.solve(ds,query['input'])
            self.assertEqual(self.solve(strong,query['input']),query['output'])

    def test_native_minority_foreground_is_retained(self):
        random.seed(1);q=task.generate()
        counts=Counter(sum(q['input'],[]));fg=q['input'][4][4]
        self.assertLess(counts[fg],max(counts.values()))
        self.assertEqual(self.solve(self.data['train'],q['input']),q['output'])

    def test_changing_demonstrated_axis_changes_prediction_for_same_query(self):
        alternate=[dict(input=p['input'],output=central_mirror_variants(p['input'])[0])
                   for p in self.data['train']]
        q=self.data['test'][0]
        expected=central_mirror_variants(q['input'])[0]
        self.assertNotEqual(expected,q['output'])
        for d4 in range(8):
            ds=apply_episode(alternate,d4,self.palette)
            g=transformed(q['input'],d4,self.palette)
            require_colour_evidence('c35c1b4c',ds,[{'input':g}],self.palette,d4)
            self.assertEqual(self.solve(ds,g),transformed(expected,d4,self.palette))

    def test_hypothesis_sets_are_d4_and_palette_closed(self):
        for p in self.data['train']+self.data['test']:
            variants=central_mirror_variants(p['input'])
            for d4 in range(8):
                observed={tuple(map(tuple,o)) for o in central_mirror_variants(transformed(p['input'],d4,self.palette))}
                expected={tuple(map(tuple,transformed(o,d4,self.palette))) for o in variants}
                self.assertEqual(observed,expected)

    def test_query_agreement_does_not_require_unique_anchor(self):
        p=dict(input=[[7]*10 for _ in range(10)],output=[[7]*10 for _ in range(10)])
        q=[[3]*10 for _ in range(10)]
        require_colour_evidence('c35c1b4c',[p],[{'input':q}])
        self.assertEqual(self.solve([p],q),q)

    def test_invalid_demo_or_geometry_fails_closed(self):
        bad=dict(input=self.data['train'][0]['input'],output=[[99]])
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('c35c1b4c',[bad],self.data['test'])
        with self.assertRaisesRegex(ValueError,'matches every'):
            self.solve([bad],self.data['test'][0]['input'])
        with self.assertRaisesRegex(ValueError,'required'):
            self.solve([],self.data['test'][0]['input'])
        with self.assertRaises(MissingColourEvidence):
            central_mirror_variants([[0]])


if __name__=='__main__':unittest.main()

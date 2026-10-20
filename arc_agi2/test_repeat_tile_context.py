"""Preserve both repetition labels; make their episode convention observable."""
import json
import unittest
from itertools import product
from arc_agi2.augmentation import apply_episode,transformed
from arc_agi2.build_million import canonical_input,digest
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.repeat_tile_context import generate_episode,repeat_variants,require_repeat_evidence
from arc_agi2.direct_factories.task_7b7f7511 import build_program
from tasks import task_7b7f7511 as native


class RepeatTileContextTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def setUp(self):
        ns={};exec(build_program(0,list(range(10))),ns);self.solve=ns['solve']

    def test_every_two_by_two_colour_pattern_has_both_reachable_labels(self):
        for bits in product(range(1,5),repeat=4):
            horizontal=native.generate(width=2,height=4,vert=0,colors=list(bits)*2)
            g=horizontal['input']
            vertical=native.generate(width=4,height=2,vert=1,colors=sum(g[:2],[]))
            self.assertEqual(g,vertical['input']);self.assertNotEqual(horizontal['output'],vertical['output'])
            self.assertEqual(repeat_variants(g),[vertical['output'],horizontal['output']])
            for expected,lesson in ((horizontal['output'],horizontal),(vertical['output'],vertical)):
                for d4 in range(8):
                    ds=apply_episode([lesson],d4,self.palette)
                    x=transformed(g,d4,self.palette)
                    self.assertEqual(self.solve(ds,x),transformed(expected,d4,self.palette))

    def test_same_query_follows_opposite_informative_demonstrations(self):
        query=native.generate(width=2,height=4,vert=0,colors=[1,2,3,1]*2)
        lesson=native.generate(width=2,height=4,vert=0,colors=[5,6,7,8]*2)
        alternate=native.generate(width=4,height=2,vert=1,colors=sum(lesson['input'][:2],[]))
        self.assertNotEqual(canonical_input(query['input']),canonical_input(lesson['input']))
        for d4 in range(8):
            q=transformed(query['input'],d4,self.palette)
            for pair,expected in ((lesson,query['output']),(alternate,query['input'][:2])):
                ds=apply_episode([pair],d4,self.palette)
                for payload in ({'input':q},dict(input=q,output=[[99]])):
                    require_colour_evidence('7b7f7511',ds,[payload],self.palette,d4)
                self.assertEqual(self.solve(ds,q),transformed(expected,d4,self.palette))

    def test_weak_or_contradictory_context_rejected(self):
        weak=native.validate()['train']
        query=native.generate(width=2,height=4,vert=0,colors=[1,2,3,1]*2)
        with self.assertRaises(MissingColourEvidence):require_repeat_evidence(weak,[{'input':query['input']}])
        with self.assertRaisesRegex(ValueError,'do not teach'):self.solve(weak,query['input'])
        alternate=dict(input=query['input'],output=query['input'][:2])
        with self.assertRaises(MissingColourEvidence):require_repeat_evidence([query,alternate],[{'input':query['input']}])
        with self.assertRaisesRegex(ValueError,'incompatible'):self.solve([query,alternate],query['input'])

    def test_generated_contexts_replay_natively_and_preserve_splits(self):
        axes=set();kinds=set()
        for seed in range(100):
            pairs,_=generate_episode(seed,canonical_input,digest,force_ambiguous_query=seed%2==0)
            self.assertEqual(len({p['canonical_input_hash'] for p in pairs}),4)
            self.assertEqual(len({p['split'] for p in pairs}),1)
            for p in pairs:
                params=json.loads(p['parameters']);axes.add(params['episode_tie_axis'])
                self.assertEqual(native.generate(**params['native_parameters']),{k:p[k] for k in ('input','output')})
                expected_split='validation' if int(canonical_input(p['input'])[:8],16)%20==0 else 'train'
                self.assertEqual(expected_split,p['split'])
            options=repeat_variants(pairs[-1]['input']);kinds.add(options[0]!=options[1])
            for d4 in range(8):
                ps=apply_episode(pairs,d4,self.palette);require_repeat_evidence(ps[:3],[{'input':ps[3]['input']}])
                self.assertEqual(self.solve(ps[:3],ps[3]['input']),ps[3]['output'])
        self.assertEqual(axes,{0,1});self.assertEqual(kinds,{False,True})

    def test_canonical_fixture_and_non_square_double_repetition_preserved(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette)
            queries=data['test']+[native.generate(width=4,height=4,vert=0,colors=[1,2,1,2]*4)]
            for p in apply_episode(queries,d4,self.palette):
                require_repeat_evidence(ds,[{'input':p['input']}]);self.assertEqual(self.solve(ds,p['input']),p['output'])

    def test_invalid_or_unsupported_grid_rejected(self):
        with self.assertRaises(MissingColourEvidence):repeat_variants([[1]])
        with self.assertRaisesRegex(ValueError,'not two copies'):self.solve(native.validate()['train'],[[1]])


if __name__=='__main__':unittest.main()

"""Retain native mirror-end piercing and grazing, learned from visible evidence."""
import unittest
import numpy as np
from tasks import task_7e2bad24 as native
from arc_agi2.augmentation import apply_episode
from arc_agi2.beam_endpoint_evidence import RULES,beam_predictions,require_endpoint_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories.task_7e2bad24 import build_program


def endpoint(kind):
    if kind=='pierce':cols=[8,10,1,8,1,1,1];lengths=[4]*7
    else:cols=[1,4,1,8,1,1,1];lengths=[4,6,4,4,4,4,4]
    return native.generate(rows=[4,8,12,2,6,10,14],cols=cols,lengths=lengths,colors=[2,2,2,3,3,3,3],prow=0,pcol=2,shown=3)


def prefix_bend():
    return native.generate(rows=[1,4,8,12,3,6,10,14],cols=[5,1,1,1,10,1,1,1],lengths=[10,4,4,4,4,4,4,4],colors=[2]*4+[3]*4,prow=0,pcol=1,shown=5)


class BeamEndpointTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def namespace(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns

    def test_weak_context_rejects_pierce_and_graze(self):
        for d4 in range(8):
            ds=apply_episode(native.validate()['train'],d4,self.palette)
            for kind in ('pierce','graze'):
                q=apply_episode([endpoint(kind)],d4,self.palette)[0]
                with self.assertRaises(MissingColourEvidence):require_endpoint_evidence(ds,[q],self.palette)
                with self.assertRaises(ValueError):self.namespace(d4)['solve'](ds,q['input'])

    def test_native_endpoint_behaviour_preserved_with_informative_demo(self):
        demonstrations=native.validate()['train']+[endpoint('pierce')]
        for d4 in range(8):
            ds=apply_episode(demonstrations,d4,self.palette)
            for kind in ('pierce','graze'):
                q=apply_episode([endpoint(kind)],d4,self.palette)[0]
                for payload in (q,{'input':q['input']},dict(q,output=[[99]])):
                    require_endpoint_evidence(ds,[payload],self.palette)
                self.assertEqual(self.namespace(d4)['solve'](ds,q['input']),q['output'])
        p=endpoint('pierce')
        self.assertTrue(any(a==2 and b==1 for ar,br in zip(p['input'],p['output']) for a,b in zip(ar,br)))

    def test_visible_prefix_bend_can_disambiguate_weak_demo_context(self):
        pair=prefix_bend();predictions=beam_predictions(pair['input'],list(range(10)))
        self.assertEqual([i for i,p in enumerate(predictions) if p is None],[2,3])
        self.assertEqual(len(set(predictions)-{None}),1)
        for d4 in range(8):
            ds=apply_episode(native.validate()['train'],d4,self.palette);q=apply_episode([pair],d4,self.palette)[0]
            require_endpoint_evidence(ds,[q],self.palette)
            self.assertEqual(self.namespace(d4)['solve'](ds,q['input']),q['output'])

    def test_counterfactual_demo_changes_endpoint_rule(self):
        p=endpoint('pierce');other=beam_predictions(p['input'],list(range(10)))[2]
        demonstrations=native.validate()['train']+[dict(p,output=[list(r) for r in other])]
        q0=endpoint('graze');target=beam_predictions(q0['input'],list(range(10)))[2]
        self.assertNotEqual([list(r) for r in target],q0['output'])
        for d4 in range(8):
            ds=apply_episode(demonstrations,d4,self.palette);q=apply_episode([dict(q0,output=[list(r) for r in target])],d4,self.palette)[0]
            require_endpoint_evidence(ds,[q],self.palette)
            self.assertEqual(self.namespace(d4)['solve'](ds,q['input']),q['output'])

    def test_independent_prefix_replay_matches_source(self):
        for d4 in range(8):
            ns=self.namespace(d4)
            for p in apply_episode([endpoint('pierce'),endpoint('graze'),prefix_bend()],d4,self.palette):
                expected=[None if not ns['_chain_ok'](np.array(p['input']),rule) else tuple(tuple(row) for row in ns['_predict'](p['input'],rule).tolist()) for rule in RULES]
                self.assertEqual(beam_predictions(p['input'],self.palette),expected)

    def test_original_fixtures(self):
        f=native.validate()
        for d4 in range(8):
            ds=apply_episode(f['train'],d4,self.palette);queries=apply_episode(f['test'],d4,self.palette)
            require_endpoint_evidence(ds,queries,self.palette)
            for q in queries:self.assertEqual(self.namespace(d4)['solve'](ds,q['input']),q['output'])

    def test_bad_or_absent_demonstrations_reject(self):
        bad={'input':[[0]],'output':[[0]]}
        for demos in ([],[bad],native.validate()['train']+[bad]):
            ds=apply_episode(demos,0,self.palette);q=apply_episode([endpoint('pierce')],0,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_endpoint_evidence(ds,[q],self.palette)
            with self.assertRaises(ValueError):self.namespace(0)['solve'](ds,q['input'])


if __name__=='__main__':unittest.main()

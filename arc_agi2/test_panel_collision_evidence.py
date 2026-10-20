"""Collision policy is demonstrated, never colour-keyed or silently defaulted."""
import unittest
import numpy as np
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.panel_collision_evidence import collision_predictions,require_collision_evidence
from arc_agi2.direct_factories.task_337b420f import build_program
from tasks import task_337b420f as native


def collision_pair(shift=True,rename=False):
    original=native.validate()['train'][0]
    mapping={4:2,5:7,6:9} if rename else {}
    colours=[mapping.get(v,v) for row in original['input'] for v in row]
    return native.generate(colors=colours,extra_color=(mapping.get(6,6) if shift else None))


class PanelCollisionTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def namespace(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns

    def test_original_fixtures_and_independent_predictions(self):
        data=native.validate()
        for d4 in range(8):
            ns=self.namespace(d4);demos=apply_episode(data['train'],d4,self.palette);queries=apply_episode(data['test'],d4,self.palette)
            require_collision_evidence(demos,queries,self.palette)
            for q in queries:self.assertEqual(ns['solve'](demos,q['input']),q['output'])
            for p in demos+queries:
                expected=[None if x is None else tuple(tuple(r) for r in x.tolist()) for x in ns['_predict'](np.array(p['input'])).values()]
                self.assertEqual(collision_predictions(p['input'],self.palette),expected)

    def test_uninformative_demos_reject_colliding_query(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'][1:],d4,self.palette);q=apply_episode([collision_pair(rename=True)],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_collision_evidence(ds,[q],self.palette)
            with self.assertRaises(ValueError):self.namespace(d4)['solve'](ds,q['input'])

    def test_demonstrated_slide_generalizes_to_other_piece_colours(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette);q=apply_episode([collision_pair(rename=True)],d4,self.palette)[0]
            for payload in (q,{'input':q['input']},dict(q,output=[[99]])):
                require_collision_evidence(ds,[payload],self.palette)
            self.assertEqual(self.namespace(d4)['solve'](ds,q['input']),q['output'])

    def test_counterfactual_overwrite_demonstration_changes_same_query_answer(self):
        data=native.validate();demos=[collision_pair(False)]+data['train'][1:]
        for d4 in range(8):
            ds=apply_episode(demos,d4,self.palette);q=apply_episode([collision_pair(False,True)],d4,self.palette)[0]
            require_collision_evidence(ds,[q],self.palette)
            self.assertEqual(self.namespace(d4)['solve'](ds,q['input']),q['output'])
            shifted=apply_episode([collision_pair(True,True)],d4,self.palette)[0]
            self.assertEqual(q['input'],shifted['input']);self.assertNotEqual(q['output'],shifted['output'])

    def test_native_latent_can_label_identical_input_differently(self):
        a,b=collision_pair(True),collision_pair(False)
        self.assertEqual(a['input'],b['input']);self.assertNotEqual(a['output'],b['output'])

    def test_invalid_demonstration_is_never_skipped(self):
        data=native.validate();bad={'input':[[8]],'output':[[8]]}
        for demos in ([],[bad],data['train']+[bad]):
            ds=apply_episode(demos,0,self.palette);q=apply_episode(data['test'],0,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_collision_evidence(ds,[q],self.palette)
            with self.assertRaises(ValueError):self.namespace(0)['solve'](ds,q['input'])


if __name__=='__main__':unittest.main()

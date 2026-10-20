"""Learn marker ray conventions without erasing native concave-marker scenes."""
import random
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.ship_docking_evidence import docking_predictions,require_docking_evidence
from arc_agi2.direct_factories.task_6e4f6532 import build_program
from tasks import task_6e4f6532 as native


def pair(seed):
    random.seed(seed)
    return native.generate()


def context(query,rule=0):
    for attempt in range(200):
        demos=[]
        for j in range(3):
            p=pair(60100+3*attempt+j)
            prediction=docking_predictions(p['input'],list(range(10)))[rule]
            if prediction is None:break
            demos.append(dict(p,output=[list(row) for row in prediction]))
        if len(demos)!=3:continue
        try:require_docking_evidence(demos,[{'input':query['input']}],list(range(10)))
        except MissingColourEvidence:continue
        return demos
    raise AssertionError('No informative context')


class ShipDockingTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    @classmethod
    def setUpClass(cls):
        cls.query=pair(60000)
        cls.demo=context(cls.query)
        predictions=docking_predictions(cls.query['input'],list(range(10)))
        truth=tuple(tuple(row) for row in cls.query['output'])
        cls.other_rule=next(i for i,p in enumerate(predictions) if p is not None and p!=truth)
        cls.other_demo=context(cls.query,cls.other_rule)
        cls.other_answer=[list(row) for row in predictions[cls.other_rule]]

    def namespace(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns

    def test_priority_sensitive_query_is_preserved_with_demonstrated_context(self):
        for d4 in range(8):
            demos=apply_episode(self.demo,d4,self.palette)
            q=apply_episode([self.query],d4,self.palette)[0]
            for payload in (q,{'input':q['input']},dict(q,output=[[99]])):
                require_docking_evidence(demos,[payload],self.palette)
            self.assertEqual(self.namespace(d4)['solve'](demos,q['input']),q['output'])

    def test_uninformative_canonical_demos_do_not_assume_native_priority(self):
        for d4 in range(8):
            demos=apply_episode(native.validate()['train'],d4,self.palette)
            q=apply_episode([self.query],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_docking_evidence(demos,[q],self.palette)
            with self.assertRaises(ValueError):self.namespace(d4)['solve'](demos,q['input'])

    def test_counterfactual_visible_rule_changes_output_on_same_query(self):
        for d4 in range(8):
            demos=apply_episode(self.other_demo,d4,self.palette)
            q=apply_episode([dict(self.query,output=self.other_answer)],d4,self.palette)[0]
            require_docking_evidence(demos,[q],self.palette)
            self.assertEqual(self.namespace(d4)['solve'](demos,q['input']),q['output'])
            original=apply_episode([self.query],d4,self.palette)[0]['output']
            self.assertNotEqual(q['output'],original)

    def test_independent_gate_predictions_match_source_for_all_d4(self):
        for d4 in range(8):
            q=apply_episode([self.query],d4,self.palette)[0]
            self.assertEqual(docking_predictions(q['input'],self.palette),self.namespace(d4)['_predictions'](q['input']))

    def test_original_fixtures_preserve_outputs_under_all_d4(self):
        data=native.validate()
        for d4 in range(8):
            demos=apply_episode(data['train'],d4,self.palette)
            queries=apply_episode(data['test'],d4,self.palette)
            require_docking_evidence(demos,queries,self.palette)
            for q in queries:self.assertEqual(self.namespace(d4)['solve'](demos,q['input']),q['output'])

    def test_missing_or_conflicting_demonstrations_reject(self):
        lesson=self.demo[0];bad=dict(lesson,output=[[0]])
        for demos in ([],[bad],[lesson,bad]):
            ds=apply_episode(demos,0,self.palette);q=apply_episode([self.query],0,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_docking_evidence(ds,[q],self.palette)
            with self.assertRaises(ValueError):self.namespace(0)['solve'](ds,q['input'])


if __name__=='__main__':unittest.main()

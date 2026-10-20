"""Distinguish chained histories from arbitrary repainting and reject ties."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.chained_lines_evidence import simulate_histories,require_chained_lines_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories.task_22425bda import build_program
from tasks import task_22425bda as native


class ChainedLinesTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def solver(self,d4,palette=None):
        ns={};exec(build_program(d4,palette or self.palette),ns);return ns['solve']

    def test_canonical_has_four_paint_orders_but_one_chain(self):
        d=native.validate();q=d['test'][0];p=list(range(10))
        self.assertEqual(len(simulate_histories(q['input'],p,False)),4)
        self.assertEqual(simulate_histories(q['input'],p),{tuple(q['output'][0])})
        for d4 in range(8):
            ds=apply_episode(d['train'],d4,self.palette);qs=apply_episode(d['test'],d4,self.palette)
            require_chained_lines_evidence(ds,qs,self.palette)
            self.assertEqual(self.solver(d4)(ds,qs[0]['input']),qs[0]['output'])

    def test_true_constructor_history_tie_rejects_under_every_augmentation(self):
        a=native.generate(size=7,colors=[2,3,4],cdirs=[0,1,2],vals=[3,3,0],allow_ambiguous=True)
        b=native.generate(size=7,colors=[3,2,4],cdirs=[1,0,2],vals=[3,3,0],allow_ambiguous=True)
        self.assertEqual(a['input'],b['input']);self.assertNotEqual(a['output'],b['output'])
        self.assertEqual(len(simulate_histories(a['input'],list(range(10)))),2)
        for d4 in range(8):
            ds=apply_episode(native.validate()['train'],d4,self.palette);q=apply_episode([a],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_chained_lines_evidence(ds,[q],self.palette)
            with self.assertRaises(ValueError):self.solver(d4)(ds,q['input'])

    def test_demo_layout_and_order_are_learned_not_d4_constants(self):
        d=native.validate()
        for p in d['train']+d['test']:p['output']=[[c] for c in p['output'][0][::-1]]
        for d4 in range(8):
            ds=apply_episode(d['train'],d4,self.palette);q=apply_episode(d['test'],d4,self.palette)[0]
            require_chained_lines_evidence(ds,[q],self.palette)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])
        for d4 in range(8):self.assertEqual(build_program(d4,self.palette),build_program(0,self.palette))

    def test_nonchain_demo_does_not_enable_pure_paint_fallback(self):
        d=native.validate();bad=dict(d['test'][0],output=[[5,4,0,1,9,3]])
        with self.assertRaises(MissingColourEvidence):require_chained_lines_evidence([bad],d['test'],list(range(10)))
        with self.assertRaises(ValueError):self.solver(0,list(range(10)))([bad],d['test'][0]['input'])

    def test_query_labels_unused(self):
        d=native.validate();q=d['test'][0]
        for payload in (q,{'input':q['input']},dict(q,output=[[99]])):require_chained_lines_evidence(d['train'],[payload],list(range(10)))

    def test_no_demonstrations_reject_instead_of_default_layout(self):
        q=native.validate()['test'][0]
        with self.assertRaises(MissingColourEvidence):require_chained_lines_evidence([],[q],list(range(10)))
        with self.assertRaises(ValueError):self.solver(0,list(range(10)))([],q['input'])

if __name__=='__main__':unittest.main()

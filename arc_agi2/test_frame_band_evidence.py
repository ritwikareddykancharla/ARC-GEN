"""Preserve rectangular fixture and distinguish edge/aspect band hypotheses."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.frame_band_evidence import band_options
from arc_agi2.direct_factories.task_3a301edc import build_program
from tasks import task_3a301edc as native


def nonsquare(variant=0):
    return native.generate(width=23+variant,height=24,row=5+variant,col=6,thicks=[2,3],colors=[4,5],extra=1)


class FrameBandEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns['solve']

    def test_original_nonsquare_fixture_kept_and_canonical_test_passes(self):
        data=native.validate();self.assertEqual(len(data['train']),5)
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette)
            for q in apply_episode(data['test'],d4,self.palette):
                require_colour_evidence('3a301edc',ds,[q],self.palette,d4)
                self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])
            q=apply_episode([data['train'][-1]],d4,self.palette)[0]
            weak=apply_episode(data['train'][:-1],d4,self.palette)
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('3a301edc',weak,[q],self.palette,d4)
            with self.assertRaises(ValueError):self.solver(d4)(weak,q['input'])

    def test_informative_nonsquare_demo_resolves_larger_margin_query(self):
        lesson=nonsquare();query=nonsquare(1)
        self.assertNotEqual(lesson['input'],query['input'])
        options=band_options(query['input'],list(range(10)))
        self.assertEqual(options[1],query['output']);self.assertNotEqual(options[0],query['output'])
        for d4 in range(8):
            weak=apply_episode(native.validate()['train'],d4,self.palette)
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('3a301edc',weak,[q],self.palette,d4)
            with self.assertRaises(ValueError):self.solver(d4)(weak,q['input'])
            for payload in (q,{'input':q['input']},{'input':q['input'],'output':[[99]]}):require_colour_evidence('3a301edc',ds,[payload],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_counterfactual_wider_band_changes_same_query(self):
        lesson=nonsquare();query=nonsquare(1);original=query['output']
        for p in (lesson,query):p['output']=band_options(p['input'],list(range(10)))[2]
        self.assertNotEqual(original,query['output'])
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('3a301edc',ds,[q],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_background_need_not_be_largest_colour(self):
        query=native.generate(width=9,height=9,row=1,col=1,thicks=[3,1],colors=[4,5])
        flat=sum(query['input'],[]);self.assertGreater(flat.count(4),flat.count(0))
        for d4 in range(8):
            ds=apply_episode(native.validate()['train'],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('3a301edc',ds,[q],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_edge_clipping_in_explicit_constructor_case(self):
        lesson=native.generate(width=19,height=20,row=1,col=4,thicks=[2,3],colors=[4,5])
        query=native.generate(width=20,height=19,row=1,col=5,thicks=[2,3],colors=[4,5])
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('3a301edc',ds,[q],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_absent_inconsistent_and_malformed_demos_reject(self):
        a=nonsquare();bad=dict(a,output=[[0]])
        for demos in ([],[bad],[a,bad]):
            ds=apply_episode(demos,0,self.palette);q=apply_episode([a],0,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('3a301edc',ds,[q],self.palette)
            with self.assertRaises(ValueError):self.solver(0)(ds,q['input'])
        malformed=nonsquare();malformed['input'][0][0]=4
        with self.assertRaises(ValueError):band_options(malformed['input'],list(range(10)))


if __name__=='__main__':unittest.main()

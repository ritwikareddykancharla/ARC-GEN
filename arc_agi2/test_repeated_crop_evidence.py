import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.direct_factories.task_4852f2fa import build_program
from tasks import task_4852f2fa as native


class RepeatedCropTests(unittest.TestCase):
    pal=[3,9,0,7,2,8,1,6,4,5]
    def solver(self,d4):
        ns={};exec(build_program(d4,self.pal),ns);return ns['solve']
    def test_original_fixtures_all_transforms(self):
        task=native.validate()
        for d in range(8):
            ds=apply_episode(task['train'],d,self.pal)
            for q in apply_episode(task['test'],d,self.pal):
                require_colour_evidence('4852f2fa',ds,[q],self.pal,d)
                self.assertEqual(self.solver(d)(ds,q['input']),q['output'])
    def test_identical_input_hidden_anchor_witness(self):
        a=native.generate(brow=2,bcol=1,prows=[1,5,7],pcols=[5,6,3],colors=[0,0,0,1,1,1,0,1,0])
        b=native.generate(brow=3,bcol=1,prows=[1,5,7],pcols=[5,6,3],colors=[1,1,1,0,1,0,0,0,0])
        self.assertEqual(a['input'],b['input']);self.assertNotEqual(a['output'],b['output'])
        ds=native.validate()['train'][:3]+native.validate()['train'][4:]
        for d in range(8):
            demos=apply_episode(ds,d,self.pal);q=apply_episode([a],d,self.pal)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('4852f2fa',demos,[q],self.pal,d)
            with self.assertRaises(ValueError):self.solver(d)(demos,q['input'])
    def test_padding_lesson_resolves_novel_short_query(self):
        lesson=native.validate()['train'][3]
        query=native.generate(brow=2,bcol=2,prows=[1,5,7],pcols=[6,7,4],colors=[0,0,0,1,1,1,0,1,0])
        for d in range(8):
            ds=apply_episode([lesson],d,self.pal);q=apply_episode([query],d,self.pal)[0]
            for payload in (q,{'input':q['input']},dict(q,output=[[99]])):require_colour_evidence('4852f2fa',ds,[payload],self.pal,d)
            self.assertEqual(self.solver(d)(ds,q['input']),q['output'])
    def test_no_reset_to_all_when_demos_conflict(self):
        t=native.validate();bad=dict(t['train'][0],output=[[0]])
        ds=apply_episode([bad],0,self.pal);q=apply_episode(t['test'],0,self.pal)[0]
        with self.assertRaises(MissingColourEvidence):require_colour_evidence('4852f2fa',ds,[q],self.pal)
        with self.assertRaises(ValueError):self.solver(0)(ds,q['input'])
    def test_program_does_not_embed_d4_axis(self):
        self.assertEqual(len({build_program(d,self.pal) for d in range(8)}),1)

if __name__=='__main__':unittest.main()

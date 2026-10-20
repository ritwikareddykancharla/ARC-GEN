"""Native motion must be learned from demos without hidden D4 signs."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.frame_motion_evidence import motion_prediction,surviving_motion_rules
from arc_agi2.direct_factories.task_5168d44c import build_program
from tasks import task_5168d44c as native


def contrary(row=3,xpose=0):
    return native.generate(width=21,height=7,row=row,col=0,idx=8,xpose=xpose)


class FrameMotionEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns['solve']

    def test_minority_side_motion_needs_demonstrated_mechanism(self):
        lesson=contrary(2);query=contrary(4)
        self.assertNotEqual(lesson['input'],query['input'])
        self.assertEqual(sum(v==3 for v in query['input'][4][:16]),8)
        self.assertEqual(sum(v==3 for v in query['input'][4][17:]),2)
        for d4 in range(8):
            weak=apply_episode(native.validate()['train'],d4,self.palette)
            strong=apply_episode([lesson]+native.validate()['train'][1:],d4,self.palette)
            q=apply_episode([query],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('5168d44c',weak,[q],self.palette,d4)
            with self.assertRaises(ValueError):self.solver(d4)(weak,q['input'])
            for payload in (q,{'input':q['input']},{'input':q['input'],'output':[[99]]}):
                require_colour_evidence('5168d44c',strong,[payload],self.palette,d4)
            self.assertEqual(self.solver(d4)(strong,q['input']),q['output'])

    def test_same_input_changes_direction_with_counterfactual_demos(self):
        lesson=contrary(2);query=contrary(4)
        for p in (lesson,query):p['output']=motion_prediction(p['input'],list(range(10)),(0,-1,-1))
        self.assertNotEqual(query['output'],contrary(4)['output'])
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('5168d44c',ds,[q],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_unseen_axis_has_no_augmentation_direction_fallback(self):
        for d4 in range(8):
            ds=apply_episode([contrary(2,1)],d4,self.palette);q=apply_episode([contrary(4)],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('5168d44c',ds,[q],self.palette,d4)
            with self.assertRaises(ValueError):self.solver(d4)(ds,q['input'])

    def test_width_parity_frame_index_and_axis_native_sweep(self):
        # All native widths, starting parity, allowed frame index and axes,
        # for height7/row3; random audit covers additional heights and rows.
        lessons=[contrary(2),contrary(2,1),native.validate()['train'][0]]
        count=0
        for d4 in range(8):
            ds=apply_episode(lessons,d4,self.palette);solve=self.solver(d4)
            for width in range(7,22):
                for col in (0,1):
                    for idx in range(1-col,(width+1-col)//2-2):
                        for xpose in (0,1):
                            p=native.generate(width=width,height=7,row=3,col=col,idx=idx,xpose=xpose)
                            q=apply_episode([p],d4,self.palette)[0]
                            self.assertEqual(solve(ds,q['input']),q['output']);count+=1
        self.assertGreater(count,1000)

    def test_fixture_tied_counts_use_observed_axis_direction(self):
        for d4 in range(8):
            ds=apply_episode(native.validate()['train'],d4,self.palette)
            for q in apply_episode(native.validate()['test'],d4,self.palette):
                require_colour_evidence('5168d44c',ds,[q],self.palette,d4)
                self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_invalid_or_conflicting_demos_reject(self):
        identity=list(range(10));a=contrary(2);b=contrary(4)
        b['output']=motion_prediction(b['input'],identity,(0,-1,-1))
        for demos in ([],[a,b],[dict(input=a['input'],output=[[0]])]):
            with self.assertRaises(MissingColourEvidence):surviving_motion_rules(demos,identity)
            ds=apply_episode(demos,0,self.palette)
            with self.assertRaises(ValueError):self.solver(0)(ds,apply_episode([a],0,self.palette)[0]['input'])


if __name__=='__main__':unittest.main()

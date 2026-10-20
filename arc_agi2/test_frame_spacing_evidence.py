"""Outliers distinguish projection separation from total object spread."""
import unittest
import common
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.frame_spacing_evidence import spacing_variants
from arc_agi2.direct_factories.task_a680ac02 import build_program
from tasks import task_a680ac02 as native


def outlier(equal_span=False,reverse_colours=False):
    rows=[0,1,12,0,10,18] if equal_span else [0,2,20,0,10,10]
    cols=[0,6,12,18,0,18] if equal_span else [0,5,10,15,0,15]
    colours=[6,5,4,3,2,1] if reverse_colours else [1,2,3,4,5,6]
    assert not common.overlaps(rows,cols,[5]*6,[5]*6,0)
    return native.generate(width=25,height=25,brows=rows,bcols=cols,colors=colours,fills=[0,0,0,1,1,1])


class FrameSpacingTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns['solve']

    def test_reachable_outlier_conflicts_with_spread_and_recovered_by_demo(self):
        query=outlier(reverse_colours=True);lesson=outlier()
        self.assertEqual(len(query['output']),4);self.assertEqual(len(query['output'][0]),12)
        self.assertNotEqual(spacing_variants(query['input'],list(range(10)))[0],spacing_variants(query['input'],list(range(10)))[1])
        weak=native.validate()['train']
        for d4 in range(8):
            ds=apply_episode(weak,d4,self.palette)
            strong=apply_episode([lesson],d4,self.palette)
            q=apply_episode([query],d4,self.palette)[0]
            for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[99]])):
                with self.assertRaises(MissingColourEvidence):require_colour_evidence('a680ac02',ds,[payload],self.palette,d4)
                require_colour_evidence('a680ac02',ds+strong,[payload],self.palette,d4)
            with self.assertRaisesRegex(ValueError,'distinguish'):self.solver(d4)(ds,q['input'])
            self.assertEqual(self.solver(d4)(ds+strong,q['input']),q['output'])

    def test_equal_spread_keeps_both_tie_conventions_under_every_orientation(self):
        query=outlier(equal_span=True);strong=outlier()
        for d4 in range(8):
            ds=apply_episode(native.validate()['train'],d4,self.palette)
            q=apply_episode([query],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('a680ac02',ds,[q],self.palette,d4)
            ds+=apply_episode([strong],d4,self.palette)
            require_colour_evidence('a680ac02',ds,[q],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_opposite_demonstrated_rule_changes_same_query_prediction(self):
        lesson=outlier();query=outlier(reverse_colours=True)
        lesson['output']=spacing_variants(lesson['input'],list(range(10)))[1]
        query['output']=spacing_variants(query['input'],list(range(10)))[1]
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('a680ac02',ds,[{'input':q['input']}],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_canonical_queries_accept_when_rules_agree(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette)
            for q in apply_episode(data['test'],d4,self.palette):
                require_colour_evidence('a680ac02',ds,[q],self.palette,d4)
                self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_invalid_frame_and_contradictory_demo_rejected(self):
        p=outlier();p['input'][1][1]=7
        with self.assertRaises(MissingColourEvidence):spacing_variants(p['input'],list(range(10)))
        p=outlier();p['output']=[[99]]
        with self.assertRaises(MissingColourEvidence):require_colour_evidence('a680ac02',[p],[{'input':p['input']}])


if __name__=='__main__':unittest.main()

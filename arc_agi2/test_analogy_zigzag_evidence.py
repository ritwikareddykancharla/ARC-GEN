"""Demonstrated analogy priorities and exhaustive finite zigzag phases."""
import copy
import unittest
from tasks import task_b0722778 as analogy,task_7447852a as zigzag
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.zigzag_evidence import frame_predictions
from arc_agi2.analogy_priority_evidence import analogy_bands


class AnalogyZigzagEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def scenes(self):
        weak=analogy.generate(xforms='RL',color_dict={},ins=[1,1,2,2,3,4,3,4],outs=[5,5,6,6,7,8,7,8])
        strong=analogy.generate(xforms='OO',color_dict={},ins=[2,1,1,1,1,2,1,1],outs=[3,4,3,3,4,3,3,3])
        query=analogy.generate(xforms='O',color_dict={},ins=[2,1,1,1],outs=[3,4,3,3])
        mapped=analogy.generate(xforms='C',color_dict={1:5,2:6},ins=[2,1,1,1],outs=[1,2,1,1])
        mapped_demo=analogy.generate(xforms='C',color_dict={3:7,4:8},ins=[4,3,3,3],outs=[3,4,3,4])
        return weak,strong,query,mapped,mapped_demo

    def check(self,tid,weak,strong,query):
        for d4 in range(8):
            ds=apply_episode(weak,d4,self.palette);ss=apply_episode(strong,d4,self.palette)
            q=apply_episode([query],d4,self.palette)[0]
            for payload in ({'input':q['input']},q,dict(input=q['input'],output=[[0]])):
                with self.subTest(tid=tid,d4=d4),self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid,ds,[payload],self.palette,d4)
            require_colour_evidence(tid,ds+ss,[{'input':q['input']}],self.palette,d4)

    def test_odd_cell_mirror_priority_needs_demonstration(self):
        weak,strong,q,_,_=self.scenes()
        self.check('b0722778',[weak],[strong],q)

    def test_recolour_priority_is_not_assumed_from_pure_geometry(self):
        weak,strong,_,q,s=self.scenes()
        self.check('b0722778',[weak,strong],[s],q)

    def test_contradictory_demo_priorities_are_rejected(self):
        _,_,q,_,_=self.scenes()
        options=analogy_bands(q['input'],0,0)[2][0][2]
        alternative=next(out for out in options.values() if out!=q['output'])
        wrong=dict(input=q['input'],output=alternative)
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('b0722778',[q,wrong],[{'input':q['input']}])

    def test_separator_corruption_is_rejected(self):
        weak,strong,q,_,_=self.scenes();wrong=copy.deepcopy(strong)
        wrong['output'][2][0]=9
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('b0722778',[weak,wrong],[{'input':q['input']}])

    def test_both_zigzag_ambiguity_classes_recover_with_evidence(self):
        for weak_width,query_width in [(13,9),(7,11)]:
            self.check('7447852a',[zigzag.generate(width=weak_width)],
                       [zigzag.generate(width=10)],zigzag.generate(width=query_width))

    def test_all_native_zigzag_widths_and_single_demo_ambiguities(self):
        pairs={w:zigzag.generate(width=w) for w in range(5,26)}
        for width,pair in pairs.items():
            for d4 in range(8):
                p=apply_episode([pair],d4,self.palette)[0]
                self.assertIn(p['output'],frame_predictions(p['input'],self.palette))
            for query_width,q in pairs.items():
                ambiguous=(width in (13,25) and query_width in (5,9,17,21)
                           or width in (7,19) and query_width in (11,15,23))
                with self.subTest(demo=width,query=query_width):
                    if ambiguous:
                        with self.assertRaises(MissingColourEvidence):
                            require_colour_evidence('7447852a',[pair],[{'input':q['input']}])
                    else:
                        require_colour_evidence('7447852a',[pair],[{'input':q['input']}])

    def test_original_episodes_pass_all_d4(self):
        for tid,module in [('7447852a',zigzag),('b0722778',analogy)]:
            data=module.validate()
            for d4 in range(8):
                ds=apply_episode(data['train'],d4,self.palette)
                qs=apply_episode(data['test'],d4,self.palette)
                require_colour_evidence(tid,ds,[{'input':q['input']} for q in qs],self.palette,d4)


if __name__=='__main__':unittest.main()

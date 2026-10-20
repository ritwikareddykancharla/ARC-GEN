import unittest
from unittest.mock import patch
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import require_colour_evidence,MissingColourEvidence
from arc_agi2.direct_factories.task_93b4f4b3 import build_program
from tasks import task_93b4f4b3 as native


def twins(order=(1,0,2)):
    return native.generate(width=3,height=2,bgcolor=5,orders=list(order),
        pattern=[2,0,0,2,0,0,0,3,0,0,3,0,4,4,4,4,4,4])


class GalleryAlignmentTests(unittest.TestCase):
    pal=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4):
        env={};exec(build_program(d4,self.pal),env);return env['solve']

    def test_translated_twins_keep_different_colours(self):
        lesson=twins((2,0,1));query=twins()
        self.assertEqual(query['output'][1][2],3)
        self.assertEqual(query['output'][4][1],2)
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.pal);q=apply_episode([query],d4,self.pal)[0]
            for payload in (q,{'input':q['input']},dict(q,output=[[99]])):
                require_colour_evidence('93b4f4b3',ds,[payload],self.pal,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_original_fixtures(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.pal)
            for q in apply_episode(data['test'],d4,self.pal):
                require_colour_evidence('93b4f4b3',ds,[q],self.pal,d4)
                self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_no_hidden_orientation_constant(self):
        self.assertEqual(len({build_program(i,self.pal) for i in range(8)}),1)

    def test_no_gallery_or_bad_demo_rejects(self):
        lesson=twins();bad=dict(lesson,output=[[0]])
        ns={};exec(build_program(0,list(range(10))),ns)
        q={'input':[[5,5,5],[5,0,5],[5,5,5]]}
        for ds,query in [([] ,lesson),([bad],lesson),([lesson],q)]:
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('93b4f4b3',ds,[query])
            with self.assertRaises(ValueError):ns['solve'](ds,query['input'])

    def test_duplicate_aligned_silhouettes_reject(self):
        q=native.generate(width=3,height=2,bgcolor=5,orders=[1,0,2],
            pattern=[2,0,0,2,0,0,3,0,0,3,0,0,4,4,4,4,4,4])
        with self.assertRaises(MissingColourEvidence):require_colour_evidence('93b4f4b3',[twins()],[q])
        ns={};exec(build_program(0,list(range(10))),ns)
        with self.assertRaises(ValueError):ns['solve']([twins()],q['input'])

    def test_empty_draw_is_skipped_before_connected(self):
        real=native.common.connected;seen=[]
        def check(points):
            self.assertTrue(points);seen.append(len(points));return real(points)
        with patch.object(native.common,'connected',side_effect=check):
            for _ in range(100):native.generate()
        self.assertGreater(len(seen),100)

if __name__=='__main__':unittest.main()

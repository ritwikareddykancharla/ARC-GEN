import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.direct_factories.task_447fd412 import build_program
from tasks import task_447fd412 as native


class ExactCoverStampTests(unittest.TestCase):
    pal=[3,9,0,7,2,8,1,6,4,5]
    def ns(self,d):
        ns={};exec(build_program(d,self.pal),ns);return ns
    def check(self,pair):
        for d in range(8):
            p=apply_episode([pair],d,self.pal)[0];ns=self.ns(d)
            self.assertEqual(ns['solve']([],p['input']),p['output'])
            old=ns['_placements'];ns['_placements']=lambda *args:list(reversed(old(*args)))
            self.assertEqual(ns['solve']([],p['input']),p['output'])
    def test_original_fixtures_including_clipped_stamp(self):
        task=native.validate()
        for pair in task['train']+task['test']:self.check(pair)
    def test_adjacent_markers_form_one_rectangular_component(self):
        p=native.generate(width=18,height=18,rows=[0,0,1,1],cols=[0,1,0,1],colors=[2,2,1,1],brows=[1,8],bcols=[1,8],bmags=[1,3]);self.check(p)
    def test_repeated_same_red_index_single_marker_case(self):
        p=native.generate(width=20,height=20,rows=[0,0,1,1],cols=[0,1,0,1],colors=[2,1,1,1],brows=[1,8,15],bcols=[1,8,15],bmags=[1,2,1]);self.check(p)
    def test_separated_marker_matching(self):
        p=native.generate(width=22,height=20,rows=[0,0,0,1],cols=[0,1,2,1],colors=[2,1,2,1],brows=[1,7,14],bcols=[1,8,1],bmags=[1,2,2]);self.check(p)
    def test_search_exhaustion_rejects_instead_of_input_fallback(self):
        q=apply_episode(native.validate()['test'],0,self.pal)[0];ns=self.ns(0);ns['NODE_LIMIT']=0
        with self.assertRaises(ValueError):ns['solve']([],q['input'])
    def test_no_template_rejects_and_no_hidden_d4(self):
        self.assertEqual(len({build_program(i,self.pal) for i in range(8)}),1)
        with self.assertRaises(ValueError):self.ns(0)['solve']([],[[self.pal[0]]*5 for _ in range(5)])

if __name__=='__main__':unittest.main()

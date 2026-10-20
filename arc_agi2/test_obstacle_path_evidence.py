"""Frozen-input routes, marker-order invariance, and demonstrated directions."""
import itertools
import unittest
from tasks import task_891232d6 as native
from arc_agi2.augmentation import apply_episode
from arc_agi2.direct_factories.task_891232d6 import build_program
from arc_agi2.obstacle_path_evidence import path_output,require_obstacle_path_evidence
from arc_agi2.colour_evidence import MissingColourEvidence


def two_paths():
    w,h=22,14;colours=[0]*(w*h)
    for row,left,right in ((7,1,3),(9,11,14)):
        for col in range(left,right+1):colours[row*w+col]=7
    return native.generate(width=w,height=h,pcols=[1,11],colors=colours)


class ObstaclePathEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def test_canonical_and_two_marker_paths_all_d4(self):
        task=native.validate()
        for d4 in range(8):
            ds=apply_episode(task['train'],d4,self.palette)
            for q in apply_episode(task['test']+[two_paths()],d4,self.palette):
                for payload in (q,{'input':q['input']},{'input':q['input'],'output':[[99]]}):require_obstacle_path_evidence(ds,[payload],self.palette)
                ns={};exec(build_program(d4,self.palette),ns)
                self.assertEqual(ns['solve'](ds,q['input']),q['output'])

    def test_start_order_does_not_change_simultaneous_output(self):
        for pair in native.validate()['train']+native.validate()['test']+[two_paths()]:
            a=path_output(pair['input'],(-1,0),(0,1),list(range(10)))
            b=path_output(pair['input'],(-1,0),(0,1),list(range(10)),reverse_starts=True)
            self.assertEqual(a,b);self.assertEqual(a,pair['output'])

    def test_native_successful_permutations_agree(self):
        for pair in native.validate()['train']+native.validate()['test']+[two_paths()]:
            g=pair['input'];starts=[c for c,v in enumerate(g[-1]) if v==6]
            colours=[0 if v==6 else v for row in g for v in row]
            for order in itertools.permutations(starts):
                candidate=native.generate(width=len(g[0]),height=len(g),pcols=order,colors=colours)
                if candidate['input'] is not None:self.assertEqual(candidate,pair)

    def test_no_hidden_d4_and_reflected_demo_changes_lateral_rule(self):
        self.assertEqual(len({build_program(d,self.palette) for d in range(8)}),1)
        pair=two_paths();ds=apply_episode([pair],4,self.palette)
        ns={};exec(build_program(0,self.palette),ns)
        self.assertEqual(ns['solve'](ds,ds[0]['input']),ds[0]['output'])

    def test_no_demo_and_wrong_demo_rejected(self):
        pair=two_paths();bad=dict(pair,output=pair['input'])
        ns={};exec(build_program(0,list(range(10))),ns)
        for ds in ([],[bad],[pair,bad]):
            with self.assertRaises(MissingColourEvidence):require_obstacle_path_evidence(ds,[pair],list(range(10)))
            with self.assertRaises(ValueError):ns['solve'](ds,pair['input'])

    def test_colliding_independent_routes_rejected(self):
        # Two markers feed one bar and try to occupy the same horizontal route.
        g=[[0]*14 for _ in range(12)]
        g[-1][1]=g[-1][5]=6
        for c in range(1,9):g[7][c]=7
        with self.assertRaises(ValueError):path_output(g,(-1,0),(0,1),list(range(10)))
        ns={};exec(build_program(0,list(range(10))),ns)
        with self.assertRaises(ValueError):ns['solve'](native.validate()['train'],g)


if __name__=='__main__':unittest.main()

import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.direct_factories.task_6cf79266 import build_program
from tasks import task_6cf79266 as native


def scene(points,side=9):
    grid=[[3]*side for _ in range(side)]
    for y,x in points:
        for r in range(y,y+3):
            for c in range(x,x+3):grid[r][c]=0
    return native.generate(colors=sum(grid,[]),size=side)


class WindowEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def solver(self,d):
        ns={};exec(build_program(d,self.palette),ns);return ns['solve']
    def test_canonical_overlap_is_demo_and_test_passes(self):
        data=native.validate()
        for d in range(8):
            demos=apply_episode(data['train'],d,self.palette)
            for q in apply_episode(data['test'],d,self.palette):
                require_colour_evidence('6cf79266',demos,[q],self.palette,d)
                self.assertEqual(self.solver(d)(demos,q['input']),q['output'])
    def test_unresolved_overlap_rejected_instead_of_consensus(self):
        lesson=scene([(1,1),(5,5)]);query=scene([(2,2),(3,3)])
        for d in range(8):
            ds=apply_episode([lesson],d,self.palette);q=apply_episode([query],d,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('6cf79266',ds,[q],self.palette,d)
            with self.assertRaises(ValueError):self.solver(d)(ds,q['input'])
    def test_informative_overlap_lesson_recovers_novel_query(self):
        lesson=scene([(1,1),(2,2)]);query=scene([(3,3),(4,4)])
        for d in range(8):
            ds=apply_episode([lesson],d,self.palette);q=apply_episode([query],d,self.palette)[0]
            for payload in (q,{'input':q['input']},dict(q,output=[[99]])):require_colour_evidence('6cf79266',ds,[payload],self.palette,d)
            self.assertEqual(self.solver(d)(ds,q['input']),q['output'])
    def test_canonical_conflicting_corner_conventions_not_d4_oracle(self):
        self.assertEqual(len({build_program(i,self.palette) for i in range(8)}),1)
    def test_no_demos_or_inconsistent_labels_reject(self):
        q=scene([(1,1)]);bad=dict(q,output=[[0]])
        for ds in ([],[bad]):
            demos=apply_episode(ds,0,self.palette);query=apply_episode([q],0,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('6cf79266',demos,[query],self.palette)
            with self.assertRaises(ValueError):self.solver(0)(demos,query['input'])

if __name__=='__main__':unittest.main()

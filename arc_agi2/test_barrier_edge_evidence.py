"""Clipped barrier pockets, edge inference, and no colour/rotation fallback."""
import unittest
from tasks import task_782b5218 as native
from arc_agi2.augmentation import apply_episode
from arc_agi2.direct_factories.task_782b5218 import build_program
from arc_agi2.barrier_edge_evidence import profile_output,region_output,require_barrier_edge_evidence
from arc_agi2.colour_evidence import MissingColourEvidence


def clipped():
    pattern=[(0,0),(1,0),(2,1),(3,1),(2,2),(1,2),(0,3)]
    grid=[[5 if (r+c)%2 else 0 for c in range(10)] for r in range(10)]
    last=None;row=7;clipped_cells=[]
    for col in (0,4,8):
        for dr,dc in pattern:
            r,c=row+dr,col+dc
            assert last is None or abs(r-last)<=1
            assert r>=0
            if r<10 and c<10:grid[r][c]=2
            else:clipped_cells.append((r,c))
            last=r
        row-=1
    assert (10,1) in clipped_cells
    return native.generate(colors=sum(grid,[]))


class BarrierEdgeEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def check(self,ds,q):
        for d in range(8):
            demos=apply_episode(ds,d,self.palette);query=apply_episode([q],d,self.palette)[0]
            for payload in (query,{'input':query['input']},{'input':query['input'],'output':[[99]]}):require_barrier_edge_evidence(demos,[payload],self.palette)
            ns={};exec(build_program(d,self.palette),ns)
            self.assertEqual(ns['solve'](demos,query['input']),query['output'])

    def test_original_fixtures_all_d4(self):
        task=native.validate()
        for q in task['test']:self.check(task['train'],q)

    def test_native_clipped_barrier_has_several_filled_pockets(self):
        q=clipped();self.check(native.validate()['train'],q)
        self.assertEqual(q['output'][9][0],5)
        self.assertEqual(q['output'][9][3],5)
        self.assertEqual(q['output'][9][6],5)
        self.assertEqual(profile_output(q['input'],'top',list(range(10))),q['output'])
        self.assertEqual(region_output(q['input'],'top',list(range(10))),q['output'])
        # The lower-left pocket consists of one cell and cannot explain other fills.
        self.assertEqual(q['input'][8][0],2);self.assertEqual(q['input'][9][1],2)

    def test_counterfactual_cleared_bottom_is_learned(self):
        task=native.validate();query=clipped()
        for p in task['train']+[query]:p['output']=region_output(p['input'],'bottom',list(range(10)))
        self.check(task['train'],query)
        self.assertEqual(len({build_program(d,self.palette) for d in range(8)}),1)

    def test_missing_or_multiple_scatter_colours_rejected(self):
        task=native.validate();ns={};exec(build_program(0,list(range(10))),ns)
        for replacements in ({5:0},{5:5}):
            grid=[[replacements.get(v,v) for v in row] for row in clipped()['input']]
            if replacements[5]==5:grid[0][0]=4
            with self.assertRaises(ValueError):ns['solve'](task['train'],grid)
            with self.assertRaises(MissingColourEvidence):require_barrier_edge_evidence(task['train'],[{'input':grid}],list(range(10)))

    def test_no_fit_has_no_d4_default(self):
        q=clipped();bad=dict(q,output=q['input']);ns={};exec(build_program(0,list(range(10))),ns)
        for ds in ([],[bad]):
            with self.assertRaises(ValueError):ns['solve'](ds,q['input'])
            with self.assertRaises(MissingColourEvidence):require_barrier_edge_evidence(ds,[q],list(range(10)))

    def test_conflicting_query_predictions_rejected(self):
        # Empty sealed region allows every edge; this must not pick a native edge.
        simple=[[0]*10 for _ in range(10)];simple[4][4]=2;simple[0][0]=5
        demo={'input':simple,'output':[[2 if v==2 else 0 for v in row] for row in simple]}
        ns={};exec(build_program(0,list(range(10))),ns)
        with self.assertRaises(ValueError):ns['solve']([demo],clipped()['input'])
        with self.assertRaises(MissingColourEvidence):require_barrier_edge_evidence([demo],[clipped()],list(range(10)))


if __name__=='__main__':unittest.main()

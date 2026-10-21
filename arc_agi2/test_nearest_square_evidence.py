import unittest
from arc_agi2.augmentation import transformed
from arc_agi2.runtime import reference
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.nearest_square_evidence import nearest_predictions,require_nearest_square_evidence
from arc_agi2.direct_factories.task_e1d2900e import build_program

PAL=list(range(10))
def scene(point):
    g=[[0]*16 for _ in range(14)]
    for r,c in [(2,2),(9,12)]:
        for y in [r,r+1]:
            for x in [c,c+1]:g[y][x]=2
    g[point[0]][point[1]]=1
    return g
class NearestSquareTests(unittest.TestCase):
    def solve(self,demos,g,pal=PAL):
        ns={};exec(build_program(0,pal),ns);return ns['solve'](demos,g)
    def test_original_nearest_diagonal_explains_freeze(self):
        task=reference('e1d2900e')['canonical']
        for p in task['train']+task['test']:self.assertEqual(self.solve(task['train'],p['input']),p['output'])
        p=task['train'][1]
        self.assertEqual(p['input'][23][13],1);self.assertEqual(p['output'][23][13],1)
        self.assertEqual(p['output'][23][19],0)
    def test_uninformative_context_rejects_tie(self):
        g=scene((2,0));out=[r[:] for r in g];out[2][0]=0;out[2][1]=1;demos=[dict(input=g,output=out)]
        q=scene((10,5))
        with self.assertRaises(MissingColourEvidence):require_nearest_square_evidence(demos,[dict(input=q)],PAL)
        with self.assertRaises(ValueError):self.solve(demos,q)
    def test_demonstrated_order_resolves_new_query(self):
        demos=reference('e1d2900e')['canonical']['train'];q=scene((10,5))
        require_nearest_square_evidence(demos,[dict(input=q)],PAL)
        self.assertEqual(self.solve(demos,q),q)
    def test_counterfactual_tie_order_can_move_point(self):
        q=scene((10,5));outs=nearest_predictions(q,PAL)
        self.assertGreater(len(set(outs)),1)
        self.assertTrue(any(o[10][11]==1 and o[10][5]==0 for o in outs))
    def test_D4_palette_and_independent_gate(self):
        task=reference('e1d2900e')['canonical'];pal=[3,9,0,7,2,8,1,6,4,5]
        for d in range(8):
            demos=[{k:transformed(p[k],d,pal) for k in ['input','output']} for p in task['train']]
            q=transformed(scene((10,5)),d,pal)
            require_nearest_square_evidence(demos,[dict(input=q)],pal)
            self.assertEqual(self.solve(demos,q,pal),q)
    def test_no_demo_or_contradictory_demo_never_falls_back(self):
        q=scene((10,5))
        with self.assertRaises(ValueError):self.solve([],q)
        bad=[r[:] for r in q];bad[0][0]=1
        with self.assertRaises(ValueError):self.solve([dict(input=q,output=bad)],q)
if __name__=='__main__':unittest.main()

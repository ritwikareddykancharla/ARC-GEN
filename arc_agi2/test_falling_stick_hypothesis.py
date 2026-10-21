"""Native-compatible six-cell hypothesis. Canonical benchmark remains unmodified."""
import random,unittest
from arc_agi2.augmentation import transformed
from arc_agi2.direct_factories.task_963c33f8 import build_program
from arc_agi2.runtime import reference
from tasks.task_963c33f8 import generate

class FallingStickHypothesisTests(unittest.TestCase):
    def solve(self,p,d4=0,palette=tuple(range(10))):
        ns={};exec(build_program(d4,palette),ns)
        return ns['solve']([],transformed(p['input'],d4,palette))
    def test_original_floor_clear_preserved(self):
        p=reference('963c33f8')['canonical']['train'][1];out=self.solve(p)
        self.assertEqual(out,p['output'])
        self.assertEqual([p['input'][13][c] for c in [8,9,10,11]],[5,5,5,5])
        self.assertEqual([out[13][c] for c in [8,9,10,11]],[7,7,5,5])
    def test_shift_is_derived_from_input_column(self):
        p=reference('963c33f8')['canonical']['train'][2];out=self.solve(p)
        columns=[c for c in range(len(p['input'][0])) if [p['input'][r][c] for r in range(3)]==[9,9,9]]
        self.assertEqual(len(columns),1);c=columns[0]
        self.assertEqual([out[r][c] for r in range(len(out)-3,len(out))],[9]*3)
        delta=[(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v!=p['output'][r][c]]
        self.assertEqual(len(delta),6)
        self.assertEqual([out[13][12],out[14][12],out[15][12]],[5,5,7])
    def test_other_original_examples_match(self):
        task=reference('963c33f8')['canonical']
        for p in [task['train'][0],task['train'][1],*task['test']]:self.assertEqual(self.solve(p),p['output'])
    def test_native_cases_reflections_rotations_and_palette(self):
        pal=[3,9,0,7,2,8,1,6,4,5];random.seed(963)
        for _ in range(12):
            p=generate()
            for d4 in range(8):self.assertEqual(self.solve(p,d4,pal),transformed(p['output'],d4,pal))
    def test_floor_clear_width_and_overwrite(self):
        size=14;colors=[7]*(size*size)
        for c in range(3,12):colors[(size-1)*size+c]=5
        p=generate(size=size,bcol=5,blues=[0,1,0],colors=colors);out=self.solve(p)
        self.assertEqual(out,p['output'])
        self.assertEqual(out[-1][3:12],[7,7,9,1,9,7,7,5,5])
if __name__=='__main__':unittest.main()

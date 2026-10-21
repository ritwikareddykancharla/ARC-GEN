"""The clipping rule preserves canonical labels and every native input case."""
import unittest
from arc_agi2.direct_factories.task_9356391f import build_program
from arc_agi2.augmentation import transformed
from arc_agi2.runtime import reference
from tasks.task_9356391f import generate,validate

class ClippedRingTests(unittest.TestCase):
    def solve(self,p,d4=0,palette=tuple(range(10))):
        ns={};exec(build_program(d4,palette),ns)
        return ns['solve']([],transformed(p['input'],d4,palette))
    def test_canonical(self):
        task=reference('9356391f')['canonical']
        self.assertEqual(validate(),task)
        for split in ['train','test']:
            for p in task[split]:self.assertEqual(self.solve(p),p['output'])
    def test_seed_column_not_a_rule(self):
        p=generate(colors=[2,3,4,8],row=9,col=3)
        self.assertEqual(p['output'][0][3],8)
        self.assertEqual(self.solve(p),p['output'])
    def test_clipping_without_seed_column_overlap(self):
        p=generate(colors=[2,3,4,8],row=13,col=6)
        self.assertEqual(p['output'][0][3],5)
        self.assertEqual(self.solve(p),p['output'])
    def test_left_right_bottom(self):
        for r,c in [(9,2),(9,13),(13,6)]:
            p=generate(colors=[2,3,4,8],row=r,col=c)
            self.assertEqual(p['output'][0][3],5)
            self.assertEqual(self.solve(p),p['output'])
    def test_legacy_latent_label_cannot_change_answer(self):
        args=dict(colors=[2,3,4,8],row=9,col=3)
        self.assertEqual(generate(**args),generate(**args,last=6))
    def test_all_orientations_and_colours(self):
        pal=[3,9,0,7,2,8,1,6,4,5]
        for r,c in [(9,3),(13,6),(9,2),(9,13)]:
            p=generate(colors=[2,3,4,8],row=r,col=c)
            for d4 in range(8):self.assertEqual(self.solve(p,d4,pal),transformed(p['output'],d4,pal))
    def test_multiple_seeds_rejected(self):
        p=generate(colors=[2,3,4,8],row=9,col=3);p['input'][4][8]=2
        with self.assertRaises(ValueError):self.solve(p)
if __name__=='__main__':unittest.main()

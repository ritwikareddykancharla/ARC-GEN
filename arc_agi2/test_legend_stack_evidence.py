"""Legend identification, demonstrated directions, and native sprite coverage."""
import random
import unittest
import common
from tasks import task_94be5b80 as native
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.legend_stack_evidence import legend_stack_options,require_legend_stack_evidence
from arc_agi2.direct_factories.task_94be5b80 import build_program


def centered(shift=0,solid=False):
    return native.generate(width=22,height=30,wide=6,tall=3,lrow=1,lcol=13,brow=6+shift,bcol=2,left=1,right=2,colors=[2,3,4],pattern='111111'*3 if solid else '010010111111001100')


class LegendStackEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def check(self,demos,query):
        for d4 in range(8):
            ds=apply_episode(demos,d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            for payload in (q,{'input':q['input']},{'input':q['input'],'output':[[99]]}):require_legend_stack_evidence(ds,[payload],self.palette)
            ns={};exec(build_program(d4,self.palette),ns)
            self.assertEqual(ns['solve'](ds,q['input']),q['output'])

    def test_fixtures_and_single_copy_extent(self):
        data=native.validate()
        for q in data['test']:self.check(data['train'],q)
        self.check([centered()],centered(1))

    def test_direction_is_learned_from_demo_not_hidden_augmentation(self):
        demo,query=centered(),centered(1);original=query['output']
        for p in (demo,query):p['output']=legend_stack_options(p['input'],list(range(10)))[-1]
        self.assertNotEqual(original,query['output'])
        self.check([demo],query)
        self.assertEqual(len({build_program(d,self.palette) for d in range(8)}),1)

    def test_solid_sprite_is_not_mistaken_for_legend(self):
        self.check([centered(solid=True)],centered(1,solid=True))

    def test_duplicate_complete_legends_are_rejected(self):
        pair=centered();grid=[row[:] for row in pair['input']]
        for r in range(20,23):
            for i,v in enumerate([2,3,4]):grid[r][13+i]=v
        with self.assertRaises(ValueError):legend_stack_options(grid,list(range(10)))
        ns={};exec(build_program(0,list(range(10))),ns)
        with self.assertRaises(ValueError):ns['solve']([pair],grid)

    def test_absent_conflicting_demo_rejected(self):
        pair=centered();other=dict(pair,output=legend_stack_options(pair['input'],list(range(10)))[-1])
        ns={};exec(build_program(0,list(range(10))),ns)
        for ds in ([],[pair,other]):
            with self.assertRaises(MissingColourEvidence):require_legend_stack_evidence(ds,[pair],list(range(10)))
            with self.assertRaises(ValueError):ns['solve'](ds,pair['input'])

    def test_native_sprite_helper_preserves_every_row_and_column(self):
        state=random.getstate()
        try:
            random.seed(940055)
            for tall in range(3,7):
                for _ in range(25):
                    points=common.diagonally_connected_sprite(3,tall)
                    self.assertEqual({r for r,c in points},set(range(tall)))
                    self.assertEqual({c for r,c in points},set(range(3)))
        finally:random.setstate(state)


if __name__=='__main__':unittest.main()

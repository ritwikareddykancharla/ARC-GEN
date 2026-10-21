"""Centre-entry stamping must preserve nonaligned and thin-bar overshoot cases."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.tile_bar_evidence import restore_tile_bars,require_tile_bar_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories.task_985ae207 import build_program
from tasks import task_985ae207 as native

THIN=dict(size=20,wides=[2,5],talls=[8,2],brows=[1,14],bcols=[8,12],bcolors=[2,4],prows=[4,9],pcols=[2,14],pcolors=[2,4],fcolor=1)
OFFSET2=dict(size=20,wides=[6,2],talls=[3,6],brows=[12,1],bcols=[5,15],bcolors=[3,2],prows=[5,3],pcols=[7,12],pcolors=[3,2],fcolor=1)


class TileBarTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def solver(self,d4,palette=None):
        ns={};exec(build_program(d4,palette or self.palette),ns);return ns['solve']

    def test_original_fixtures_all_orientations(self):
        d=native.validate()
        for d4 in range(8):
            ds=apply_episode(d['train'],d4,self.palette);qs=apply_episode(d['test'],d4,self.palette)
            require_tile_bar_evidence(ds,qs,self.palette)
            self.assertEqual(self.solver(d4)(ds,qs[0]['input']),qs[0]['output'])

    def test_thin_bar_far_edge_overshoot_and_offset2_preserved(self):
        cases=[native.generate(**THIN),native.generate(**OFFSET2)]
        self.assertEqual(cases[0]['output'][16][13:16],[1,1,1])
        self.assertEqual(cases[1]['output'][15][6:9],[1,1,1])
        for palette in (list(range(10)),self.palette):
            for d4 in range(8):
                for q in apply_episode(cases,d4,palette):
                    require_tile_bar_evidence([],[q],palette)
                    self.assertEqual(restore_tile_bars(q['input'],palette),q['output'])
                    self.assertEqual(self.solver(d4,palette)([],q['input']),q['output'])

    def test_query_labels_unused(self):
        d=native.validate();q=native.generate(**THIN)
        for payload in (q,{'input':q['input']},dict(q,output=[[99]])):require_tile_bar_evidence(d['train'],[payload],list(range(10)))

    def test_archived_far_edge_guard_is_rejected_as_demo(self):
        q=native.generate(**THIN);wrong=[row[:] for row in q['output']]
        for y in range(14,17):
            for x in range(13,16):wrong[y][x]=q['input'][y][x]
        bad=dict(q,output=wrong)
        with self.assertRaises(MissingColourEvidence):require_tile_bar_evidence([bad],[q],list(range(10)))
        with self.assertRaises(ValueError):self.solver(0,list(range(10)))([bad],q['input'])

    def test_diagonal_and_jumped_bar_inputs_reject(self):
        q=native.generate(**THIN)
        for ny,nx in ((11,2),(4,1)):
            g=[row[:] for row in q['input']]
            for y in range(3,6):
                for x in range(1,4):g[y][x]=8
            for dy in(-1,0,1):
                for dx in(-1,0,1):g[ny+dy][nx+dx]=2 if(dy,dx)==(0,0) else 1
            with self.assertRaises(MissingColourEvidence):require_tile_bar_evidence([],[{'input':g}],list(range(10)))
            with self.assertRaises(ValueError):self.solver(0,list(range(10)))([],g)

    def test_d4_does_not_supply_direction(self):
        for d4 in range(8):self.assertEqual(build_program(d4,self.palette),build_program(0,self.palette))

if __name__=='__main__':unittest.main()

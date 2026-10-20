"""Retain tied/soft scenes while requiring evidence for consequential choices."""
import random
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.legend_tile_evidence import tile_variants
from arc_agi2.symmetry_selection_evidence import symmetry_variants
from tasks import task_a32d8b75 as stamp, task_8e5c0c38 as symmetry


class SelectionTileEvidenceTests(unittest.TestCase):
    palette = [3,9,0,7,2,8,1,6,4,5]
    hard = [[1,1,1],[1,1,2],[1,2,1]]
    soft = [[1,2],[2,1]]

    def pair(self,tile,arrow,anchor='tl'):
        return stamp.generate(legends=[dict(side='left',width=5,tile=tile,
            tile_pos=(1,1),shape=[[1,1],[1,0]],shape_color=3,shape_pos=(6,1),
            box_col=1,anchor=anchor,arrow=arrow)],canvas=[[5]*18 for _ in range(20)])

    def test_soft_tiles_cannot_alone_teach_swap(self):
        weak = self.pair(self.soft,'right')
        query = self.pair(self.hard,'right')
        strong = stamp.validate()['train']
        self.check_tile_ambiguity([weak],strong,query,weak)

    def test_up_arrows_cannot_teach_whether_tile_rotates(self):
        weak = self.pair(self.hard,'up')
        query = self.pair(self.hard,'right')
        strong = self.pair(self.hard,'left')
        self.check_tile_ambiguity([weak],[strong],query,weak)

    def check_tile_ambiguity(self,weak,strong,query,agreed):
        for d4 in range(8):
            ds = apply_episode(weak,d4,self.palette)
            ss = apply_episode(strong,d4,self.palette)
            q,a = apply_episode([query,agreed],d4,self.palette)
            with self.subTest(d4=d4):
                for q0 in ({'input':q['input']},q,dict(input=q['input'],output=[[0]])):
                    with self.assertRaises(MissingColourEvidence):
                        require_colour_evidence('a32d8b75',ds,[q0],self.palette,d4)
                require_colour_evidence('a32d8b75',ds+ss,[{'input':q['input']}],self.palette,d4)
                require_colour_evidence('a32d8b75',ds,[{'input':a['input']}],self.palette,d4)

    def test_native_tile_output_and_survivor_sets_transform_consistently(self):
        state = random.getstate()
        try:
            random.seed(32875)
            pairs = [stamp.generate() for _ in range(12)]
            pairs += [self.pair([[1,1,2],[2,1,1]],'right',a) for a in ('tl','tr','bl','br')]
            for pair in pairs:
                original = tile_variants(pair['input'],list(range(10)),0)
                for d4 in range(8):
                    p = apply_episode([pair],d4,self.palette)[0]
                    variants = tile_variants(p['input'],self.palette,d4)
                    self.assertEqual(variants[16],p['output'])
                    expected = {tuple(map(tuple,apply_episode([dict(input=pair['input'],output=v)],d4,self.palette)[0]['output']))
                                for v in original if v is not None}
                    observed = {tuple(map(tuple,v)) for v in variants if v is not None}
                    self.assertEqual(expected,observed)
        finally: random.setstate(state)

    def test_canonical_stamp_episodes_pass(self):
        data = stamp.validate()
        for d4 in range(8):
            ds = apply_episode(data['train'],d4,self.palette)
            qs = apply_episode(data['test'],d4,self.palette)
            require_colour_evidence('a32d8b75',ds,[{'input':q['input']} for q in qs],self.palette,d4)

    def test_symmetry_tie_evidence_preserves_hard_queries(self):
        data = symmetry.validate()
        strong = symmetry.generate(width=16,height=16,background=0,shapes=[dict(
            colour=1,top=2,left=2,w=5,core=[(r,c) for r in [0,2,5] for c in [0,4]],
            extras=[(r,7) for r in [0,2,5]])])
        for d4 in range(8):
            ds = apply_episode(data['train'],d4,self.palette)
            ss = apply_episode([strong],d4,self.palette)
            q,agreed = apply_episode(data['test'],d4,self.palette)
            with self.subTest(d4=d4):
                for query in ({'input':q['input']},q,dict(input=q['input'],output=[[0]])):
                    with self.assertRaises(MissingColourEvidence):
                        require_colour_evidence('8e5c0c38',ds,[query],self.palette,d4)
                require_colour_evidence('8e5c0c38',ds+ss,[{'input':q['input']}],self.palette,d4)
                require_colour_evidence('8e5c0c38',ds,[{'input':agreed['input']}],self.palette,d4)

    def test_symmetry_orientation_and_tie_hypotheses_are_d4_closed(self):
        state = random.getstate()
        try:
            random.seed(85038)
            for tie in (0,1):
                for _ in range(5):
                    pair = symmetry.generate(tie_rate=tie)
                    original = symmetry_variants(pair['input'])
                    self.assertIn(pair['output'],original)
                    for d4 in range(8):
                        p = apply_episode([pair],d4,self.palette)[0]
                        expected = {tuple(map(tuple,apply_episode([dict(input=pair['input'],output=v)],d4,self.palette)[0]['output'])) for v in original}
                        observed = {tuple(map(tuple,v)) for v in symmetry_variants(p['input'])}
                        self.assertEqual(expected,observed)
        finally: random.setstate(state)


if __name__ == '__main__': unittest.main()

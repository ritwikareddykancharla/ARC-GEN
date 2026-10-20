"""Retain off-grid and hidden-centre fixtures without layer-ranking guesses."""
import unittest
from collections import Counter
from arc_agi2.augmentation import apply_episode
from arc_agi2.corner_frames_evidence import unique_corner_assembly,require_corner_frame_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories.task_4290ef0e import build_program
from tasks import task_4290ef0e as native


class CornerFramesTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def solver(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns['solve']

    def test_all_original_fixtures_and_all_d4_palette(self):
        d=native.validate()
        for d4 in range(8):
            ds=apply_episode(d['train'],d4,self.palette);qs=apply_episode(d['test'],d4,self.palette)
            require_corner_frame_evidence(ds,qs,self.palette)
            for q in ds+qs:self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_hidden_background_centre_is_not_dropped(self):
        d=native.validate()
        for p in (d['train'][0],d['test'][0]):
            bg=Counter(sum(p['input'],[])).most_common(1)[0][0]
            m=len(set(sum(p['input'],[]))-{bg})
            self.assertEqual(len(p['output']),2*m+1)
            self.assertEqual(p['output'][m][m],bg)
            self.assertEqual(unique_corner_assembly(p['input']),p['output'])

    def test_original_off_grid_centres_remain_supported(self):
        # Exact native validate() cases: train3 centres at col=-1,row=height;
        # query also has row=height. No in-grid-centre preference remains.
        d=native.validate()
        for p in (d['train'][2],d['test'][0]):self.assertEqual(unique_corner_assembly(p['input']),p['output'])

    def test_query_labels_unused(self):
        d=native.validate();q=d['test'][0]
        for payload in (q,{'input':q['input']},dict(q,output=[[99]])):require_corner_frame_evidence(d['train'],[payload])

    def test_contradictory_demo_and_background_tie_reject(self):
        d=native.validate();bad=dict(d['train'][0],output=[[99]])
        with self.assertRaises(MissingColourEvidence):require_corner_frame_evidence([bad],d['test'])
        with self.assertRaises(ValueError):self.solver(0)([bad],d['test'][0]['input'])
        tied=[[1,2],[2,1]]
        with self.assertRaises(ValueError):unique_corner_assembly(tied)
        with self.assertRaises(ValueError):self.solver(0)([],tied)

    def test_no_orientation_palette_or_layer_priority(self):
        for d4 in range(8):self.assertEqual(build_program(d4,self.palette),build_program(0,list(range(10))))
        self.assertNotIn('centred',build_program(0,self.palette))
        self.assertNotIn('fallback',build_program(0,self.palette))

if __name__=='__main__':unittest.main()

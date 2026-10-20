"""Visible reconstruction must reject unobserved residues instead of guessing."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.wallpaper_evidence import unique_wallpaper_patch,require_wallpaper_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories.task_abbfd121 import build_program
from tasks import task_abbfd121 as native


class WallpaperEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns['solve']

    def test_original_fixtures_all_orientations_and_palette(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette)
            for q in apply_episode(data['test'],d4,self.palette):
                require_wallpaper_evidence(ds,[q],self.palette)
                self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_hidden_residue_identical_input_different_answer_is_rejected(self):
        pattern=[1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,4]
        kw=dict(width=6,height=6,size=4,wides=[2,3],talls=[2,3],brows=[0,3],bcols=[0,3],bcolors=[8,9])
        a=native.generate(**kw,pattern=pattern)
        b=native.generate(**kw,pattern=pattern[:-1]+[5])
        self.assertEqual(a['input'],b['input']);self.assertNotEqual(a['output'],b['output'])
        for d4 in range(8):
            q=apply_episode([a],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_wallpaper_evidence([],[q])
            with self.assertRaises(ValueError):self.solver(d4)([],q['input'])

    def test_query_answer_never_enters_gate_or_program(self):
        data=native.validate();q=data['test'][0]
        for payload in ({'input':q['input']},q,dict(q,output=[[99]])):
            require_wallpaper_evidence(data['train'],[payload])
        self.assertEqual(self.solver(0)(data['train'],q['input']),q['output'])

    def test_contradictory_demo_rejected_not_overridden(self):
        data=native.validate();bad=dict(data['train'][0],output=[[99]])
        with self.assertRaises(MissingColourEvidence):require_wallpaper_evidence([bad],data['test'])
        with self.assertRaises(ValueError):self.solver(0)([bad],data['test'][0]['input'])

    def test_no_occluders_no_raw_crop_fallback(self):
        for g in ([[1]*20 for _ in range(20)],[[1,2],[2,1]]):
            with self.assertRaises(ValueError):unique_wallpaper_patch(g)
            with self.assertRaises(ValueError):self.solver(0)([],g)

    def test_emitted_program_has_no_orientation_or_palette_oracle(self):
        for d4 in range(8):self.assertEqual(build_program(d4,self.palette),build_program(0,list(range(10))))

if __name__=='__main__':unittest.main()

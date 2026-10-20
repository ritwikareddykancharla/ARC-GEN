"""Recover mirror rules from evidence, including native ambiguous rectangles."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.occluded_symmetry_evidence import reflection_options,require_occluded_symmetry_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories.task_3345333e import build_program
from tasks import task_3345333e as native


def scene(height,width,tall,off,bcol):
    return native.generate(rows=[r for r in range(height) for c in range(width)],cols=[c for r in range(height) for c in range(width)],srow=5,scol=7,brow=7,bcol=bcol,wide=4,tall=tall,colors=[2,3],off=off,flip=0)


class OccludedSymmetryTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def solver(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns['solve']

    def test_original_fixtures_all_orientations_and_palette(self):
        d=native.validate()
        for d4 in range(8):
            ds=apply_episode(d['train'],d4,self.palette);qs=apply_episode(d['test'],d4,self.palette)
            require_occluded_symmetry_evidence(ds,qs,self.palette)
            for q in qs:self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_native_ambiguous_rectangles_need_direction_evidence(self):
        weak=scene(2,4,4,1,8);q=scene(4,2,5,0,9)
        # Both half-sprites contain8 connected pixels and use native default parameter ranges.
        options=reflection_options(q['input'],list(range(10)))
        self.assertNotEqual(options[0,4],options[1,4])
        for d4 in range(8):
            ds=apply_episode([weak],d4,self.palette);query=apply_episode([q],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_occluded_symmetry_evidence(ds,[query],self.palette)
            with self.assertRaises(ValueError):self.solver(d4)(ds,query['input'])
            ds=apply_episode(native.validate()['train'],d4,self.palette)
            require_occluded_symmetry_evidence(ds,[query],self.palette)
            self.assertEqual(self.solver(d4)(ds,query['input']),query['output'])

    def test_counterfactual_demo_can_change_which_rectangle_is_removed(self):
        q=scene(4,2,5,0,9);alternate=next(iter(reflection_options(q['input'],list(range(10)))[0,4]))
        wrong=dict(q,output=[list(row) for row in alternate])
        self.assertNotEqual(wrong['output'],q['output'])
        for d4 in range(8):
            ds=apply_episode([scene(2,4,4,1,8),wrong],d4,self.palette);query=apply_episode([wrong],d4,self.palette)[0]
            require_occluded_symmetry_evidence(ds,[query],self.palette)
            self.assertEqual(self.solver(d4)(ds,query['input']),query['output'])

    def test_query_answer_not_used(self):
        d=native.validate();q=d['test'][0]
        for payload in (q,{'input':q['input']},dict(q,output=[[99]])):
            require_occluded_symmetry_evidence(d['train'],[payload],list(range(10)))

    def test_no_demo_or_inconsistent_demo_rejects(self):
        d=native.validate();bad=dict(d['train'][0],output=[[99]])
        for ds in ([],[bad]):
            with self.assertRaises(MissingColourEvidence):require_occluded_symmetry_evidence(ds,d['test'],list(range(10)))
            with self.assertRaises(ValueError):self.solver(0)(ds,d['test'][0]['input'])

    def test_d4_argument_does_not_supply_direction(self):
        for d4 in range(8):self.assertEqual(build_program(d4,self.palette),build_program(0,self.palette))

if __name__=='__main__':unittest.main()

"""Distinguish symmetry rules with demos; preserve transverse-symmetric decoys."""
import unittest
from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence,require_colour_evidence
from arc_agi2.object_symmetry_evidence import symmetry_options
from arc_agi2.direct_factories.task_72ca375d import build_program
from tasks import task_72ca375d as native

RECT={(0,0),(0,1),(1,0),(1,1)}
LR={(0,0),(0,1),(0,2),(1,1)}
TB={(0,0),(1,0),(1,1),(2,0)}
ASYM={(0,0),(0,1),(1,0)}
ASYM2={(0,0),(1,0),(2,0),(2,1)}


def scene(target=RECT,second=TB,variant=0):
    rows=[];cols=[];idxs=[]
    for i,cells in enumerate((target,second,ASYM2)):
        for r,c in sorted(cells):rows.append(r);cols.append(c);idxs.append(i)
    return native.generate(rows=rows,cols=cols,idxs=idxs,colors=[2,3,4],
                           brows=[1+variant,5,6],bcols=[1,6-variant,1],size=10)


def crop(cells,colour):
    return [[colour if (r,c) in cells else 0 for c in range(max(c for r,c in cells)+1)]
            for r in range(max(r for r,c in cells)+1)]


class ObjectSymmetryEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]

    def solver(self,d4):
        ns={};exec(build_program(d4,self.palette),ns);return ns['solve']

    def test_transverse_symmetric_decoy_needs_informative_context(self):
        weak=scene(second=ASYM);strong=scene();query=scene(variant=1)
        self.assertNotEqual(strong['input'],query['input'])
        opts=symmetry_options(query['input'],list(range(10)))
        self.assertEqual([len(x) for x in opts],[1,2,1])
        for d4 in range(8):
            w=apply_episode([weak],d4,self.palette);s=apply_episode([strong],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('72ca375d',w,[q],self.palette,d4)
            with self.assertRaises(ValueError):self.solver(d4)(w,q['input'])
            for payload in (q,{'input':q['input']},{'input':q['input'],'output':[[99]]}):require_colour_evidence('72ca375d',s,[payload],self.palette,d4)
            self.assertEqual(self.solver(d4)(s,q['input']),q['output'])

    def test_counterfactual_axis_changes_selected_object_on_same_query(self):
        lesson=scene(target=LR);query=scene(target=LR,variant=1)
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([query],d4,self.palette)[0]
            require_colour_evidence('72ca375d',ds,[q],self.palette,d4)
            self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])
            changed=dict(lesson,output=crop(TB,3));other=dict(query,output=crop(TB,3))
            ds2=apply_episode([changed],d4,self.palette);q2=apply_episode([other],d4,self.palette)[0]
            require_colour_evidence('72ca375d',ds2,[q2],self.palette,d4)
            self.assertNotEqual(q['output'],q2['output'])
            self.assertEqual(self.solver(d4)(ds2,q2['input']),q2['output'])

    def test_multiple_matching_objects_have_no_scan_order_tiebreak(self):
        p=scene(second=RECT);lesson=scene(target=LR)
        for d4 in range(8):
            ds=apply_episode([lesson],d4,self.palette);q=apply_episode([p],d4,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('72ca375d',ds,[q],self.palette,d4)
            with self.assertRaises(ValueError):self.solver(d4)(ds,q['input'])

    def test_canonical_single_axis_shapes_retain_original_outputs(self):
        data=native.validate()
        for d4 in range(8):
            ds=apply_episode(data['train'],d4,self.palette)
            for q in apply_episode(data['test'],d4,self.palette):
                require_colour_evidence('72ca375d',ds,[q],self.palette,d4)
                self.assertEqual(self.solver(d4)(ds,q['input']),q['output'])

    def test_prediction_sets_closed_under_all_d4(self):
        p=scene(target=LR)
        base=symmetry_options(p['input'],list(range(10)))
        for d4 in range(8):
            q=apply_episode([p],d4,self.palette)[0];observed=symmetry_options(q['input'],self.palette)
            expected=[]
            for options in base:
                pairs=[dict(input=p['input'],output=[list(r) for r in out]) for out in options]
                expected.append(frozenset(tuple(tuple(r) for r in x['output']) for x in apply_episode(pairs,d4,self.palette)))
            self.assertEqual(set(expected),{frozenset(x) for x in observed})

    def test_no_demos_and_inconsistent_labels_reject(self):
        lesson=scene(target=LR);bad=dict(lesson,output=[[0]])
        for ds in ([],[bad],[lesson,bad]):
            demos=apply_episode(ds,0,self.palette);q=apply_episode([lesson],0,self.palette)[0]
            with self.assertRaises(MissingColourEvidence):require_colour_evidence('72ca375d',demos,[q],self.palette)
            with self.assertRaises(ValueError):self.solver(0)(demos,q['input'])


if __name__=='__main__':unittest.main()

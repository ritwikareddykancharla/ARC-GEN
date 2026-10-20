"""Visible-band contract fixes unobservable dimensions, not erased blocks."""
import copy
import json
import unittest
from unittest.mock import patch
from tasks import task_80214e03 as native
from arc_agi2.augmentation import apply_episode
from arc_agi2.direct_factories.task_80214e03 import build_program
from arc_agi2.mosaic_band_evidence import visible_mosaic,require_mosaic_band_evidence
from arc_agi2.colour_evidence import MissingColourEvidence


def block_hole(colour=4):
    return dict(width=9,height=9,brow=1,bcol=1,wides=[3,3],talls=[3,3],colors=[1,2,3,colour],prows=[r for r in range(3,6) for c in range(3,6)],pcols=[c for r in range(3,6) for c in range(3,6)])


def erased_column():
    return dict(width=12,height=9,brow=1,bcol=1,wides=[3,3,3],talls=[3,3],colors=[1,2,5,3,4,6],prows=[r for r in range(6) for c in range(6,9)],pcols=[c for r in range(6) for c in range(6,9)])


class MosaicBandEvidenceTests(unittest.TestCase):
    palette=[3,9,0,7,2,8,1,6,4,5]
    def test_original_fixtures_all_d4(self):
        task=native.validate()
        for d in range(8):
            ds=apply_episode(task['train'],d,self.palette);qs=apply_episode(task['test'],d,self.palette)
            ns={};exec(build_program(d,self.palette),ns)
            for q in qs:
                for payload in (q,{'input':q['input']},{'input':q['input'],'output':[[99]]}):require_mosaic_band_evidence(ds,[payload],self.palette)
                self.assertEqual(ns['solve'](ds,q['input']),q['output'])

    def test_completely_erased_internal_block_remains_ambiguous(self):
        a,vis=native._generate(**block_hole(4));b,vis2=native._generate(**block_hole(5))
        self.assertTrue(vis and vis2);self.assertEqual(a['input'],b['input']);self.assertNotEqual(a['output'],b['output'])
        ns={};exec(build_program(0,list(range(10))),ns)
        with self.assertRaises(ValueError):visible_mosaic(a['input'],list(range(10)))
        with self.assertRaises(ValueError):ns['_recover'](a['input'])

    def test_only_completely_erased_bands_trigger_native_resampling(self):
        rejected,visible=native._generate(**erased_column());self.assertFalse(visible)
        accepted= native.validate()['test'][0]
        with patch.object(native,'_generate',side_effect=[(rejected,False),(accepted,True)]) as sampler:
            self.assertEqual(native.generate(),accepted);self.assertEqual(sampler.call_count,2)
        # Explicit historical inputs remain exactly reproducible, including witness.
        self.assertEqual(native.generate(**erased_column()),rejected)
        # Restoring one pixel makes the band observable; no minimum-density rule.
        args=erased_column();args['prows']=args['prows'][1:];args['pcols']=args['pcols'][1:]
        _,visible=native._generate(**args);self.assertTrue(visible)

    def test_partial_erasures_and_same_colour_neighbours_retained(self):
        args=dict(width=11,height=11,brow=1,bcol=1,wides=[3,3,3],talls=[3,3,3],colors=[1,1,2,3,4,4,5,6,7],prows=[0,1,2,3,4,5,6,7,8],pcols=[0,1,2,3,4,5,6,7,8])
        q,visible=native._generate(**args);self.assertTrue(visible)
        blocks=visible_mosaic(q['input'],list(range(10)))
        self.assertEqual([r[::-1] for r in blocks],q['output'])

    def test_mirror_axis_learned_without_d4_constant(self):
        task=native.validate();query=task['test'][0]
        for p in task['train']+[query]:p['output']=visible_mosaic(p['input'],list(range(10)))[::-1]
        ns={};exec(build_program(0,list(range(10))),ns)
        require_mosaic_band_evidence(task['train'],[query],list(range(10)))
        self.assertEqual(ns['solve'](task['train'],query['input']),query['output'])
        self.assertEqual(len({build_program(d,self.palette) for d in range(8)}),1)

    def test_no_demos_and_conflicting_demos_reject(self):
        task=native.validate();q=task['test'][0];bad=dict(task['train'][0],output=[[0]])
        ns={};exec(build_program(0,list(range(10))),ns)
        for ds in ([],[bad]):
            with self.assertRaises(ValueError):ns['solve'](ds,q['input'])
            with self.assertRaises(MissingColourEvidence):require_mosaic_band_evidence(ds,[q],list(range(10)))


if __name__=='__main__':unittest.main()

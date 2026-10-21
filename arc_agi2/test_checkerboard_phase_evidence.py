"""Context enrichment must never masquerade as solving the original fixture."""
import copy
import unittest
from .augmentation import transformed
from .checkerboard_phase_evidence import gate
from .colour_evidence import MissingColourEvidence, require_colour_evidence
from .direct_factories.task_df8cc377 import build_program
from .fixture_policy import fixture_basis
from .runtime import reference
from tasks import task_df8cc377 as native

PAL = [3,9,0,7,2,8,1,6,4,5]

def augment(pairs,d,pal):
    return [{k:transformed(v,d,pal) for k,v in p.items()} for p in pairs]

class CheckerboardEvidenceTest(unittest.TestCase):
    def test_original_preserved_and_enrichment_native(self):
        p=reference('df8cc377'); c=p['canonical']; t=p['teaching_fixture']
        self.assertEqual(t['train'][:-1],c['train']); self.assertEqual(t['test'],c['test'])
        self.assertEqual(c,native.validate())
        self.assertEqual(t['train'][-1],native.generate(width=10,height=10,wides=[4,3],talls=[3,5],brows=[0,4],bcols=[0,6],bgcolors=[1,2],fgcolors=[3,4],prows=[6,8,9],pcols=[1,2,4],pcolors=[3,4,4]))
        self.assertFalse(fixture_basis('df8cc377')['original_fixture_context_passed'])

    def test_original_abstains_enriched_solves_all_augmentations(self):
        packet=reference('df8cc377')
        for pal in (list(range(10)),PAL):
            for d in range(8):
                ns={};exec(build_program(d,pal),ns)
                c=packet['canonical']; demos=augment(c['train'],d,pal); qs=augment(c['test'],d,pal)
                self.assertIsNone(ns['solve'](demos,qs[0]['input']))
                self.assertEqual(gate(demos,qs[0]['input'])['status'],'phase_context_shortfall')
                with self.assertRaises(MissingColourEvidence):require_colour_evidence('df8cc377',demos,qs,pal,d)
                demos=augment(packet['teaching_fixture']['train'],d,pal)
                require_colour_evidence('df8cc377',demos,qs,pal,d)
                for q in qs:self.assertEqual(ns['solve'](demos,q['input']),q['output'])
                poisoned=copy.deepcopy(qs)
                for q in poisoned:q['output']=[[-999]]
                require_colour_evidence('df8cc377',demos,poisoned,pal,d)

    def test_d4_does_not_choose_phase(self):
        self.assertEqual(len({build_program(d,PAL) for d in range(8)}),1)

    def test_contradictory_demonstration_rejected(self):
        p=reference('df8cc377')['teaching_fixture']; ds=copy.deepcopy(p['train'])
        ds[0]['output'][0][0]=123
        with self.assertRaises(MissingColourEvidence):require_colour_evidence('df8cc377',ds,p['test'])
        ns={};exec(build_program(0,list(range(10))),ns)
        self.assertIsNone(ns['solve'](ds,p['test'][0]['input']))

if __name__=='__main__':unittest.main()

"""Band completion must not guess invisible phase or overfit a one-cell suffix."""
import hashlib
import json
from pathlib import Path
import unittest

from tasks import task_90f3ed37 as bands
from .augmentation import transformed
from .direct_factories.task_90f3ed37 import build_program


PALETTE=[3,9,0,7,2,8,1,6,4,5]


class BandPhaseRepair(unittest.TestCase):
    def test_identical_input_has_two_latent_phases(self):
        data=json.loads((Path(__file__).parent/'reports/90f3ed37-hidden-phase-witness.json').read_text())
        first=bands.generate(**data['first_parameters'])
        second=bands.generate(**data['second_parameters'])
        self.assertEqual(first,data['first'])
        self.assertEqual(second,data['second'])
        self.assertEqual(first['input'],second['input'])
        self.assertNotEqual(first['output'],second['output'])
        self.assertFalse(bands._unambiguous(first,10,15))
        self.assertFalse(bands._unambiguous(second,10,15))
        for d4 in range(8):
            ns={};exec(build_program(d4,PALETTE),ns)
            with self.assertRaisesRegex(ValueError,'unique band continuation'):
                ns['solve']([],transformed(first['input'],d4,PALETTE))

    def test_original_zigzag_and_other_fixtures_all_orientations(self):
        fixture=bands.validate()
        for pair in fixture['train']+fixture['test']:
            for d4 in range(8):
                ns={};exec(build_program(d4,PALETTE),ns)
                self.assertEqual(ns['solve']([],transformed(pair['input'],d4,PALETTE)),
                                 transformed(pair['output'],d4,PALETTE))
        pair=fixture['train'][2];g=pair['input'];h,w=len(g),len(g[0])
        candidates=bands._explanations({(c,r) for r in range(h) for c in range(w) if g[r][c]==8},w,h)
        expected=frozenset((c,r) for r in range(h) for c in range(w) if g[r][c]!=pair['output'][r][c])
        self.assertEqual(set(candidates),{expected})

    def test_original_fixtures_unchanged(self):
        digest=hashlib.sha256(json.dumps(bands.validate(),sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest,'0cdb5078c300e70e954f4be1e642e6022b69cdba97402b154b5bb2921898d2bf')


if __name__=='__main__':
    unittest.main()

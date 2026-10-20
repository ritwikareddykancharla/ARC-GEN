"""Recover hidden cross centres and adjacent defects without arbitrary ties."""
import hashlib
import json
from pathlib import Path
import random
import unittest
from unittest.mock import patch

from tasks import task_50846271 as crosses, task_8dab14c2 as l_shapes
from .augmentation import transformed
from .direct_factories.task_50846271 import build_program as cross_program
from .direct_factories.task_8dab14c2 import build_program as l_program


REPORTS=Path(__file__).parent/'reports'
PALETTE=[3,9,0,7,2,8,1,6,4,5]


def read(name):
    return json.loads((REPORTS/name).read_text())


def namespace(factory,d4,palette=PALETTE):
    ns={};exec(factory(d4,palette),ns)
    return ns


class CrossLRepairs(unittest.TestCase):
    def test_hidden_cross_centre_without_red_column(self):
        data=read('50846271-execution-counterexample.json')
        pair=data['episode']['train'][2]
        palette=[PALETTE[x] for x in data['palette']]
        for d4 in range(8):
            self.assertEqual(namespace(cross_program,d4,palette)['solve']([],transformed(pair['input'],d4,PALETTE)),
                             transformed(pair['output'],d4,PALETTE))

    def test_hidden_arm_length_is_not_resolved_by_shortest_preference(self):
        witness=read('50846271-hidden-length-witness.json')
        first,second=witness['first'],witness['second']
        self.assertEqual(first['input'],second['input'])
        self.assertNotEqual(first['output'],second['output'])
        for pair in [first,second]:
            h,w=len(pair['input']),len(pair['input'][0])
            self.assertEqual(crosses.generate(width=w,height=h,colors=sum(pair['output'],[])),pair)
            self.assertFalse(crosses._scene_is_determined(pair))
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError,'unique cross completion'):
                namespace(cross_program,d4)['solve']([],transformed(first['input'],d4,PALETTE))

    def test_unoccluded_cross_centres_are_not_hidden_by_double_paint(self):
        state=random.getstate()
        try:
            random.seed(571)
            with patch.object(crosses.common,'random_pixels',return_value=[]):
                colours=crosses._sample_colors(25,25)
            self.assertIn(2,colours)
            self.assertNotIn(8,colours)
        finally:
            random.setstate(state)

    def test_cross_search_exhaustion_is_not_a_guessed_answer(self):
        ns=namespace(cross_program,0);ns['_NODE_CAP']=0
        with self.assertRaisesRegex(RuntimeError,'search budget exhausted'):
            ns['solve']([],transformed(crosses.validate()['test'][0]['input'],0,PALETTE))

    def test_original_clipped_cross_fixtures(self):
        fixture=crosses.validate()
        for pair in fixture['train']+fixture['test']:
            for d4 in range(8):
                self.assertEqual(namespace(cross_program,d4)['solve']([],transformed(pair['input'],d4,PALETTE)),
                                 transformed(pair['output'],d4,PALETTE))

    def test_adjacent_l_defects_saved_failure(self):
        data=read('8dab14c2-execution-counterexample.json');e=data['episode']
        pairs=e['train']+[dict(input=q['input'],output=o) for q,o in zip(e['test'],e['solutions'])]
        palette=[PALETTE[x] for x in data['palette']]
        for pair in pairs:
            for d4 in range(8):
                self.assertEqual(namespace(l_program,d4,palette)['solve']([],transformed(pair['input'],d4,PALETTE)),
                                 transformed(pair['output'],d4,PALETTE))

    def test_multiple_l_explanations_do_not_choose_fewest_defects(self):
        data=read('8dab14c2-ambiguity-witness.json');pair=data['pair']
        self.assertGreater(len(data['outputs']),1)
        self.assertIn(pair['output'],data['outputs'])
        self.assertFalse(l_shapes._unambiguous(pair['input'],pair['output']))
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError,'unique L-shape defect'):
                namespace(l_program,d4)['solve']([],transformed(pair['input'],d4,PALETTE))

    def test_original_fixtures_unchanged(self):
        for module,digest in [(crosses,'ac823da921929db50aaf8075ea3bbf7047d3ef377ef690fc75b10c2cdbdef9b2'),
                              (l_shapes,'3f374f5d9661f344f67282f4e9c96d34e346701cc7da6a5be51572762006e054')]:
            self.assertEqual(hashlib.sha256(json.dumps(module.validate(),sort_keys=True).encode()).hexdigest(),digest)


if __name__=='__main__':
    unittest.main()

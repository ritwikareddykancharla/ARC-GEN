"""Keep recoverable overlaps and use marker-connected flood regions."""
import hashlib
import json
from pathlib import Path
import random
import unittest

from tasks import task_52df9849 as shapes, task_1190bc91 as floods
from .augmentation import transformed
from .direct_factories.task_52df9849 import build_program as shape_program
from .direct_factories.task_1190bc91 import build_program as flood_program


REPORTS=Path(__file__).parent/'reports'
PALETTE=[3,9,0,7,2,8,1,6,4,5]


def read(name):
    return json.loads((REPORTS/name).read_text())


def namespace(factory,d4):
    ns={};exec(factory(d4,PALETTE),ns)
    return ns


class OcclusionMarkerRepairs(unittest.TestCase):
    def test_covered_staircase_is_retained(self):
        data=read('52df9849-recoverable-covered-staircase.json')
        pair=shapes.generate(**data['parameters'])
        self.assertEqual(pair,data['pair'])
        for d4 in range(8):
            self.assertEqual(namespace(shape_program,d4)['solve']([],transformed(pair['input'],d4,PALETTE)),
                             transformed(pair['output'],d4,PALETTE))

    def test_hidden_staircase_corner_has_multiple_outputs(self):
        data=read('52df9849-ambiguity-witness.json');pair=data['pair']
        outputs=shapes._visible_outputs(pair['input'],7)
        self.assertGreater(len(outputs),1)
        self.assertIn(tuple(map(tuple,pair['output'])),outputs)
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError,'unique layer-reversal'):
                namespace(shape_program,d4)['solve']([],transformed(pair['input'],d4,PALETTE))

    def test_fixture_same_layer_bounding_boxes_may_overlap(self):
        pair=shapes.validate()['test'][1]
        for d4 in range(8):
            self.assertEqual(namespace(shape_program,d4)['solve']([],transformed(pair['input'],d4,PALETTE)),
                             transformed(pair['output'],d4,PALETTE))

    def test_six_object_scene_is_not_dropped_by_packing(self):
        state=random.getstate()
        try:
            random.seed(195845306567961)
            pair=shapes.generate()
        finally:
            random.setstate(state)
        self.assertEqual(len({v for row in pair['input'] for v in row}-{7}),6)
        self.assertEqual(shapes._visible_outputs(pair['input'],7),{tuple(map(tuple,pair['output']))})

    def test_legacy_marker_mismatch_preserved_but_program_follows_marker(self):
        data=read('1190bc91-marker-region-mismatch.json')
        pair=floods.generate(**data['parameters'])
        self.assertEqual(pair,data['original_pair'])
        self.assertNotEqual(pair['output'],data['visible_flood_output'])
        for d4 in range(8):
            self.assertEqual(namespace(flood_program,d4)['solve']([],transformed(pair['input'],d4,PALETTE)),
                             transformed(data['visible_flood_output'],d4,PALETTE))

    def test_marker_fixtures_all_orientations(self):
        fixture=floods.validate()
        for pair in fixture['train']+fixture['test']:
            for d4 in range(8):
                self.assertEqual(namespace(flood_program,d4)['solve']([],transformed(pair['input'],d4,PALETTE)),
                                 transformed(pair['output'],d4,PALETTE))

    def test_conflicting_flood_markers_do_not_choose_reading_order(self):
        grid=[[0]*10 for _ in range(10)]
        for c,colour in zip(range(6,10),(3,4,5,6)):grid[5][c]=colour
        for r in (4,5):grid[r][0]=2
        for r in (6,7):grid[r][0]=7
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError,'share a flood region'):
                namespace(flood_program,d4)['solve']([],transformed(grid,d4,PALETTE))

    def test_original_fixtures_unchanged(self):
        for module,digest in [(shapes,'c8a5902d5d9f4b3db02d5f79cd77571860f1979b70812aba5f7e6415a281c8a3'),
                              (floods,'633b18868273cd1288cf7d1247a7368cc33f8495738e0fb33ec29558812bc7d8')]:
            self.assertEqual(hashlib.sha256(json.dumps(module.validate(),sort_keys=True).encode()).hexdigest(),digest)


if __name__=='__main__':
    unittest.main()

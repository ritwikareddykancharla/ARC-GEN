"""Retain recoverable weak rings and reject invisible colour identity ties."""
import hashlib
import json
import unittest
from pathlib import Path

from tasks import task_652646ff as rings, task_6cbe9eb8 as frames, task_ce602527 as sprites
from .augmentation import transformed
from .direct_factories.task_652646ff import build_program as ring_program
from .direct_factories.task_6cbe9eb8 import build_program as frame_program
from .direct_factories.task_ce602527 import build_program as sprite_program


REPORTS = Path(__file__).parent / 'reports'
PALETTE = [3,9,0,7,2,8,1,6,4,5]


def read(name):
    return json.loads((REPORTS/name).read_text())


class RingFrameSpriteRepairs(unittest.TestCase):
    def test_identifiable_weak_top_rings_are_retained(self):
        cases = read('652646ff-weak-top-probe.json')['examples']
        for key,item in cases.items():
            if not key.startswith('unique_top_'):
                continue
            pair = rings.generate(**item['parameters'])
            self.assertEqual(pair,item['pair'])
            self.assertLess(item['visible_top_cells'],8)
            self.assertEqual(rings._ring_orders(pair['input'])[1],{(1,2)})
            for d4 in range(8):
                ns = {}
                exec(ring_program(d4,PALETTE),ns)
                self.assertEqual(ns['solve']([],transformed(pair['input'],d4,PALETTE)),
                                 transformed(pair['output'],d4,PALETTE))

    def test_ambiguous_ring_colour_is_not_decided_by_numeric_rank(self):
        item = read('652646ff-weak-top-probe.json')['examples']['ambiguous']
        pair = rings.generate(**item['parameters'])
        self.assertEqual(pair,item['pair'])
        self.assertGreater(len(rings._ring_orders(pair['input'])[1]),1)
        for d4 in range(8):
            ns = {}
            exec(ring_program(d4,PALETTE),ns)
            with self.assertRaisesRegex(ValueError,'not uniquely determined'):
                ns['solve']([],transformed(pair['input'],d4,PALETTE))

    def check_saved_pairs(self,tid,build):
        data = read(f'{tid}-execution-counterexample.json')
        self.assertEqual(data['d4'],0)
        composed = [PALETTE[v] for v in data['palette']]
        for d4 in range(8):
            ns = {}
            exec(build(d4,composed),ns)
            for pair in data['episode']['train']:
                self.assertEqual(ns['solve']([],transformed(pair['input'],d4,PALETTE)),
                                 transformed(pair['output'],d4,PALETTE))

    def test_noise_dots_are_not_extra_rings(self):
        self.check_saved_pairs('652646ff',ring_program)

    def test_four_fragment_frame_is_not_background_texture(self):
        self.check_saved_pairs('6cbe9eb8',frame_program)

    def test_solid_inside_solid_already_rejected_by_original_generator(self):
        pair = frames.generate(width=21,height=12,bgwidth=2,bgheight=2,
                               pattern=[0,1,1,0],wides=[7,5],talls=[7,5],
                               brows=[2,3],bcols=[4,5],outers=[3,4],inners=[3,4])
        self.assertEqual(pair,{'input':None,'output':None})

    def test_two_matching_sprite_colours_are_ambiguous(self):
        data = read('ce602527-execution-counterexample.json')
        grid = data['episode']['train'][1]['input']
        for d4 in range(8):
            ns = {}
            exec(sprite_program(d4,PALETTE),ns)
            with self.assertRaisesRegex(ValueError,'one output sprite'):
                ns['solve']([],transformed(grid,d4,PALETTE))

    def test_original_fixtures_unchanged(self):
        for module,expected in [
            (rings,'5c709fb9452cce4b1d2f42f57ac5bc5f16c3eb2013fe83c63fed63ac7d12d46d'),
            (frames,'fa5516284affbfa31767bebaa01a4abfb753800ec321cf6dd51246dad3f65edb'),
            (sprites,'6aa588231027a199e994aa5a75e4c4d3b7ee680358e9613a483f0be2e8a6bb78'),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(module.validate(),sort_keys=True).encode()).hexdigest(),expected)


if __name__=='__main__':
    unittest.main()

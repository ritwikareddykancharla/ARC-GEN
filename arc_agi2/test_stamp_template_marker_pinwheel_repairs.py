"""Reject hidden colour-order labels while preserving edge-touching solutions."""
import hashlib
import json
import unittest
from pathlib import Path

from tasks import task_5b37cb25 as stamps, task_8a004b2b as templates
from tasks import task_b7256dcd as markers, task_e40b9e2f as pinwheels
from .augmentation import transformed
from .direct_factories.task_5b37cb25 import build_program as stamp_program
from .direct_factories.task_8a004b2b import build_program as template_program
from .direct_factories.task_b7256dcd import build_program as marker_program
from .direct_factories.task_e40b9e2f import build_program as pinwheel_program


REPORTS = Path(__file__).parent/'reports'
PALETTE = [3,9,0,7,2,8,1,6,4,5]


def read(name):
    return json.loads((REPORTS/name).read_text())


class StampTemplateMarkerPinwheelRepairs(unittest.TestCase):
    def test_conflicting_stamp_order_is_invisible(self):
        data = read('5b37cb25-hidden-order-witness.json')
        first = stamps.generate(**data['first_parameters'])
        second = stamps.generate(**data['second_parameters'])
        self.assertEqual(first,data['first'])
        self.assertEqual(second,data['second'])
        self.assertEqual(first['input'],second['input'])
        self.assertNotEqual(first['output'],second['output'])
        for d4 in range(8):
            ns = {}
            exec(stamp_program(d4,PALETTE),ns)
            with self.assertRaisesRegex(ValueError,'different colours'):
                ns['solve']([],transformed(first['input'],d4,PALETTE))

    def test_repeated_template_columns_have_multiple_outputs(self):
        pair = read('8a004b2b-execution-counterexample.json')['native_train'][2]
        self.assertGreater(len(templates._visible_outputs(pair['input'])),1)
        for d4 in range(8):
            ns = {}
            exec(template_program(d4,PALETTE),ns)
            with self.assertRaisesRegex(ValueError,'one output'):
                ns['solve']([],transformed(pair['input'],d4,PALETTE))

    def test_approved_scaled_template_can_touch_frame_edge(self):
        pair = templates.validate()['test'][0]
        self.assertTrue(any(v not in (0,4) for v in pair['output'][-1]))
        for d4 in range(8):
            ns = {}
            exec(template_program(d4,PALETTE),ns)
            self.assertEqual(ns['solve']([],transformed(pair['input'],d4,PALETTE)),
                             transformed(pair['output'],d4,PALETTE))

    def test_two_marker_colours_on_same_cell_do_not_choose_scan_order(self):
        pair = read('b7256dcd-execution-counterexample.json')['native_train'][2]
        colours = [v for row in pair['input'] for v in row]
        self.assertEqual(markers.generate(width=len(pair['input'][0]),
                                         height=len(pair['input']),colors=colours),pair)
        for d4 in range(8):
            ns = {}
            exec(marker_program(d4,PALETTE),ns)
            with self.assertRaisesRegex(ValueError,'conflicting marker'):
                ns['solve']([],transformed(pair['input'],d4,PALETTE))

    def test_same_colour_markers_can_share_a_component(self):
        grid = [[7,7,1,7],[6,6,6,7],[7,7,1,7]]
        expected = [[7]*4,[1,1,1,7],[7]*4]
        for d4 in range(8):
            ns = {}
            exec(marker_program(d4,PALETTE),ns)
            self.assertEqual(ns['solve']([],transformed(grid,d4,PALETTE)),
                             transformed(expected,d4,PALETTE))

    def test_latent_pinwheel_is_not_always_the_minimum_completion(self):
        data = read('e40b9e2f-execution-counterexample.json')
        pair = data['native_train'][2]
        self.assertFalse(pinwheels._unambiguous(pair['input'],pair['output']))
        self.assertEqual(data['minimum_added'],11)
        self.assertNotEqual(pair['output'],data['minimum_completion'])
        for d4 in range(8):
            ns = {}
            exec(pinwheel_program(d4,PALETTE),ns)
            self.assertEqual(ns['solve']([],transformed(pair['input'],d4,PALETTE)),
                             transformed(data['minimum_completion'],d4,PALETTE))

    def test_original_fixtures_unchanged(self):
        for module,expected in [
            (stamps,'ecabfbc17aef7c803bc1da45e7abb07ac992792cd4157a91a43a1e19f873e222'),
            (templates,'90eafd40a35094bfcd937a7543175e6bc0974a2e758bdc9d862fe2e84ae0299b'),
            (markers,'66a45da366597b99a987088364fd86acbeeff3608fbf994c14939c53e92d838f'),
            (pinwheels,'77a3898ea9af400ac919c8d38227f580ae8c4d88692f24c0570b435289069a2b'),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(module.validate(),sort_keys=True).encode()).hexdigest(),expected)


if __name__=='__main__':
    unittest.main()

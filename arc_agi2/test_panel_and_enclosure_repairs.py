"""Regression cases distinguish disconnected panel pixels and enclosed pockets."""
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tasks import task_8698868d as panels, task_7b6016b9 as enclosure
from .augmentation import transformed
from .direct_factories.task_8698868d import build_program as panel_program
from .direct_factories.task_7b6016b9 import build_program as enclosure_program


def witness(tid):
    return json.loads((Path(__file__).parent / 'reports' /
                       f'{tid}-execution-counterexample.json').read_text())


class PanelAndEnclosureRepairs(unittest.TestCase):
    def test_isolated_panel_cell_is_not_a_loose_shape(self):
        data = witness('8698868d')
        pair = data['episode']['train'][1]
        for d4 in range(8):
            for palette in [list(range(10)), [3,9,0,7,2,8,1,6,4,5]]:
                ns = {}
                exec(panel_program(d4, palette), ns)
                self.assertEqual(ns['solve']([], transformed(pair['input'],d4,palette)),
                                 transformed(pair['output'],d4,palette))

    def test_old_random_label_disagrees_with_connectivity(self):
        pair = witness('7b6016b9')['native_pair']
        grid = pair['input']
        self.assertFalse(enclosure._labels_match_connectivity(grid, pair['output'],
                                                               len(grid[0]), len(grid)))
        ns = {}
        exec(enclosure_program(0, list(range(10))), ns)
        corrected = ns['solve']([], grid)
        self.assertNotEqual(corrected, pair['output'])
        self.assertTrue(enclosure._labels_match_connectivity(grid, corrected,
                                                              len(grid[0]), len(grid)))
        self.assertEqual(corrected[16][5], 2)
        for d4 in range(8):
            palette = [3,9,0,7,2,8,1,6,4,5]
            ns = {}
            exec(enclosure_program(d4, palette), ns)
            self.assertEqual(ns['solve']([], transformed(grid,d4,palette)),
                             transformed(corrected,d4,palette))

    def test_enclosure_sampling_exhaustion_is_explicit(self):
        with patch.object(enclosure, '_MAX_ATTEMPTS', 0):
            with self.assertRaisesRegex(RuntimeError, 'attempt budget'):
                enclosure.generate()

    def test_original_fixtures_unchanged(self):
        for module, expected in [
            (panels, '82046948787896c407a8cf8d50e847b619b23a27eaf7f0037268c32cd809123d'),
            (enclosure, 'e21acd95f6e6b2f605aacdec4bbbe403808359eea0ad80c53e5747681ca67242'),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(module.validate(),sort_keys=True).encode()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()

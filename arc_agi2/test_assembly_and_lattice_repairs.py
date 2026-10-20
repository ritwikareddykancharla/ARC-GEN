"""Reject ambiguous assemblies and restore the lattice beneath displaced markers."""
import hashlib
import json
import unittest
from pathlib import Path

from tasks import task_83b6b474 as assembly, task_97239e3d as lattice
from .augmentation import transformed
from .direct_factories.task_83b6b474 import build_program as assembly_program
from .direct_factories.task_97239e3d import build_program as lattice_program


def witness(tid):
    return json.loads((Path(__file__).parent / 'reports' /
                       f'{tid}-execution-counterexample.json').read_text())


class AssemblyAndLatticeRepairs(unittest.TestCase):
    def test_two_ring_assemblies_are_rejected_without_arbitrary_tie_break(self):
        data = witness('83b6b474')
        self.assertEqual(assembly.count_tilings(data['output_size'], data['ambiguous_border']), 2)
        grid = data['episode']['train'][1]['input']
        for d4 in range(8):
            palette = [3,9,0,7,2,8,1,6,4,5]
            ns = {}
            exec(assembly_program(d4, palette), ns)
            with self.assertRaisesRegex(ValueError, 'uniquely determined'):
                ns['solve']([], transformed(grid,d4,palette))

    def test_original_ring_fixtures_have_unique_assemblies(self):
        task = assembly.validate()
        for pair in task['train'] + task['test']:
            output = pair['output']
            n = len(output)
            border = [output[y][x] for y,x in assembly._ring_coords(n,4*(n-1))]
            self.assertEqual(assembly.count_tilings(n,border), 1)

    def test_markers_on_ring_cells_are_erased_before_painting(self):
        data = witness('97239e3d')
        self.assertEqual(data['d4'], 0)
        for d4 in range(8):
            palette = [3,9,0,7,2,8,1,6,4,5]
            # Counterexample already has its saved palette applied.
            composed = [palette[v] for v in data['palette']]
            ns = {}
            exec(lattice_program(d4, composed), ns)
            for pair in data['episode']['train']:
                self.assertEqual(ns['solve']([],transformed(pair['input'],d4,palette)),
                                 transformed(pair['output'],d4,palette))

    def test_nested_rectangles_have_shared_centres(self):
        self.assertTrue(lattice._shares_center([0,12,4,8],[0,12,4,8],[1,1,2,2]))
        self.assertFalse(lattice._shares_center([0,4,8,12],[0,4,8,12],[1,1,2,2]))

    def test_original_fixtures_unchanged(self):
        for module, expected in [
            (assembly, '805478c9be2aa3435a0bb743495b743d851ee1635ee4a25e17a7dd78cb3cbe76'),
            (lattice, '5d1bb8fdbae96f83249b9ad32c14c316a71f8183258d2db341a9cd9e055f6be7'),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(module.validate(),sort_keys=True).encode()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()

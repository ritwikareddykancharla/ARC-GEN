"""Reject demonstrated synthetic label ambiguities without changing fixtures."""
import json
import random
import unittest
from pathlib import Path

from tasks import task_0e206a2e as markers
from tasks import task_150deff5 as bricks
from tasks import task_1d61978c as diagonals
from tasks import task_228f6490 as holes
from .runtime import call, grid, reference


class ConstructorUniqueness(unittest.TestCase):
    def counterexample(self, task_id):
        path = Path(__file__).parent / "reports/regression-cases"
        return json.loads((path / f"{task_id}-ambiguous-input.json").read_text())["input"]

    def test_distinct_brick_colourings_are_rejected(self):
        scene = self.counterexample("150deff5")
        cells = {(r, c) for r, row in enumerate(scene)
                 for c, value in enumerate(row) if value == 5}
        self.assertEqual(bricks._num_distinct_colourings(cells), 2)
        for pairs in bricks.validate().values():
            for pair in pairs:
                cells = {(r, c) for r, row in enumerate(pair["input"])
                         for c, value in enumerate(row) if value == 5}
                self.assertEqual(bricks._num_distinct_colourings(cells), 1)

    def test_two_marker_assignments_are_rejected(self):
        scene = self.counterexample("0e206a2e")
        # Recover the two visible source sprites by their known counterexample
        # bounding boxes; no output or hidden transform is supplied to the check.
        params = {"rows": [], "cols": [], "idxs": [], "colors": [],
                  "brows": [0, 0], "bcols": [0, 0]}
        for idx, (r0, r1, c0, c1) in enumerate(((2, 6, 13, 16), (6, 8, 2, 7))):
            for r in range(r0, r1):
                for c in range(c0, c1):
                    if scene[r][c] == 0:
                        continue
                    for key, value in (("rows", r), ("cols", c),
                                       ("idxs", idx), ("colors", scene[r][c])):
                        params[key].append(value)
        self.assertFalse(markers._unambiguous({"input": scene}, params))

    def test_original_fixture_inputs_and_labels_are_unchanged(self):
        for tid, module in (("0e206a2e", markers), ("150deff5", bricks),
                            ("1d61978c", diagonals), ("228f6490", holes)):
            expected = reference(tid)["canonical"]
            for split, pairs in module.validate().items():
                self.assertCountEqual(pairs, expected[split])

    def test_dust_indistinguishable_from_a_piece_is_rejected(self):
        scene = self.counterexample("228f6490")
        self.assertGreater(len(holes._visible_outputs(scene)), 1)
        for pairs in holes.validate().values():
            for pair in pairs:
                self.assertTrue(holes._is_unambiguous(pair["input"], pair["output"]))

    def test_previously_timing_out_diagonal_seeds_finish(self):
        state = random.getstate()
        try:
            for seed in (176550225061674, 175472539387530, 151255485137070):
                random.seed(seed)
                for _ in range(4):
                    pair = call(diagonals.generate, seconds=5)
                    grid(pair["input"])
                    grid(pair["output"])
        finally:
            random.setstate(state)

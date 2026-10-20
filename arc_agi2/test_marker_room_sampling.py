"""Count preservation, room topology and visible demonstration evidence."""
import hashlib
import json
import random
import unittest
from unittest.mock import patch

import common
from arc_agi2.runtime import call
from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import (
    MissingColourEvidence, _colour_components, require_colour_evidence)
from tasks import task_d2abd087, task_e39e9282, task_e681b708, task_6a1e5592


class MarkerRoomSamplingTests(unittest.TestCase):
    def setUp(self):
        self.state = random.getstate()
        random.seed(273)

    def tearDown(self):
        random.setstate(self.state)

    def test_six_sprites_remain_distinct_with_size_based_paint(self):
        real, first = common.randint, True

        def choose(low, high):
            nonlocal first
            if first:
                first = False
                return 6
            return real(low, high)

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_d2abd087.generate, seconds=5)
        components = list(_colour_components(pair["input"], 5))
        self.assertEqual(len(components), 6)
        for cells in components:
            self.assertTrue(4 <= len(cells) <= 8)
            ink = 2 if len(cells) == 6 else 1
            self.assertTrue(all(pair["output"][r][c] == ink for r, c in cells))

    def test_absorbing_square_accepts_five_distinct_marker_destinations(self):
        with patch.object(common, "randint", return_value=5):
            markers = task_e39e9282._sample_markers(9, [3], [3], [6])
        self.assertIsNotNone(markers)
        prows, pcols, pidxs = markers
        self.assertEqual(len(prows), 5)
        pair = task_e39e9282.generate(
            size=9, brows=[3], bcols=[3], bcolors=[6],
            prows=prows, pcols=pcols, pidxs=pidxs)
        self.assertIsNotNone(pair["input"])
        self.assertEqual(sum(v == 9 for row in pair["input"] for v in row), 5)
        self.assertEqual(sum(v == 9 for row in pair["output"] for v in row), 5)
        self.assertTrue(all(3 <= r <= 5 and 3 <= c <= 5
                            for r, row in enumerate(pair["output"])
                            for c, v in enumerate(row) if v == 9))

    def test_crowded_markers_keep_seven_blocks(self):
        settings, real = iter([6, 1, 7]), common.randint

        def choose(low, high):
            value = next(settings, None)
            return real(low, high) if value is None else value

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_e39e9282.generate, seconds=5)
        self.assertEqual(len(pair["input"]), 13)
        blocks = list(_colour_components(pair["input"], 5))
        blocks += list(_colour_components(pair["input"], 6))
        self.assertEqual(len(blocks), 7)
        self.assertTrue(all(len(c) == 9 for c in blocks))

    def test_partial_walls_keep_rectangular_rooms_but_reject_l_shapes(self):
        self.assertTrue(task_e681b708._rectangular_rooms([
            [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [1, 1, 1, 0, 0],
            [0, 0, 1, 0, 0], [0, 0, 1, 0, 0]]))
        self.assertFalse(task_e681b708._rectangular_rooms([
            [0, 0, 0], [0, 1, 1], [0, 0, 0]]))

    def test_large_rooms_still_generate_two_dot_colours(self):
        real = common.randint

        def choose(low, high):
            if (low, high) == (18, 28): return 28
            if (low, high) == (-2, 2): return 2
            return real(low, high)

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_e681b708.generate, seconds=5)
        g, out = pair["input"], pair["output"]
        self.assertEqual((len(g), len(g[0])), (30, 30))
        dots = [(r, c) for r in range(30) for c in range(30) if g[r][c] != out[r][c]]
        self.assertTrue(dots)
        self.assertGreaterEqual(len({out[r][c] for r, c in dots}), 2)
        cleared = [row[:] for row in g]
        for r, c in dots:
            self.assertEqual(g[r][c], 1)
            cleared[r][c] = 0
        self.assertTrue(task_e681b708._rectangular_rooms(cleared))

    def test_unseen_size_branch_and_block_role_rejected(self):
        size6 = task_d2abd087.generate(
            rows=[0, 0, 0, 1, 1, 1], cols=[0, 1, 2, 0, 1, 2],
            idxs=[0]*6, brows=[2], bcols=[2])
        size5 = task_d2abd087.generate(
            rows=[0, 0, 0, 1, 1], cols=[0, 1, 2, 0, 1],
            idxs=[0]*5, brows=[2], bcols=[2])
        dissolve = task_e39e9282.generate(
            size=9, brows=[3], bcols=[3], bcolors=[5],
            prows=[1], pcols=[-1], pidxs=[0])
        absorb = task_e39e9282.generate(
            size=9, brows=[3], bcols=[3], bcolors=[6],
            prows=[1], pcols=[-1], pidxs=[0])
        palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
        for tid, first, second in (
            ("d2abd087", size6, size5), ("e39e9282", dissolve, absorb)):
            for d4 in range(8):
                demos = [{k: transformed(p[k], d4, palette)
                          for k in ("input", "output")} for p in (first, second)]
                query = [{"input": transformed(second["input"], d4, palette)}]
                with self.assertRaises(MissingColourEvidence):
                    require_colour_evidence(tid, demos[:1], query, palette, d4)
                require_colour_evidence(tid, demos, query, palette, d4)

    def test_fixture_hashes_unchanged(self):
        for module, digest in [
            (task_d2abd087, "317e2b4e23a3746c19583d7f49a243a6ec1aa7da128f9685a63c1e5929307e61"),
            (task_e39e9282, "7df2c006609821e7f27d9253c8aec3793d325b252c5688f4853251b3ddea3e2d"),
            (task_e681b708, "648d68b1a76ec4b08dd7ea812486710d4cd3de276c3b9a5ef77fb2be3b4795ac"),
            (task_6a1e5592, "ff3792f64e141be97a3806869575861eb8bcdcada18ebe4005d8e85de237f46d"),
        ]:
            self.assertEqual(hashlib.sha256(json.dumps(
                module.validate(), sort_keys=True).encode()).hexdigest(), digest)

    def test_pairwise_distinct_footprints_can_still_be_ambiguous(self):
        g = [[int(v) for v in row] for row in [
            "222222222222222", "222222222222222", "000220020200202",
            "000000000000000", "000000000000000", "000000000000000",
            "000005505055000", "000005555055000", "555005550055050",
            "555505550005050"]]
        self.assertIsNone(task_6a1e5592._unique_fit(g))

    def test_supplied_shape_fits_have_one_complete_painting(self):
        for pairs in task_6a1e5592.validate().values():
            for pair in pairs:
                painted = frozenset(
                    (r, c) for r, row in enumerate(pair["output"])
                    for c, v in enumerate(row) if v == 1)
                self.assertEqual(task_6a1e5592._unique_fit(pair["input"]), painted)
                self.assertIsNone(task_6a1e5592._unique_fit(pair["input"], max_nodes=0))

    def test_four_fitting_pieces_are_preserved(self):
        real, first = common.randint, True

        def choose(low, high):
            nonlocal first
            if first:
                first = False
                return 4
            return real(low, high)

        with patch.object(common, "randint", side_effect=choose):
            pair = call(task_6a1e5592.generate, seconds=5)
        self.assertEqual(len(list(_colour_components(pair["input"], 5))), 4)
        painted = frozenset((r, c) for r, row in enumerate(pair["output"])
                            for c, v in enumerate(row) if v == 1)
        self.assertEqual(task_6a1e5592._unique_fit(pair["input"]), painted)


if __name__ == "__main__":
    unittest.main()

"""Sampling must preserve ARC sizes and the information needed to solve a pair."""
import hashlib
import importlib
import json
import random
import unittest
from unittest.mock import patch

import common
from arc_agi2.runtime import call, grid
from tasks import task_d749d46f, task_e21a174a, task_e6721834, task_e74e1818


class SamplingDomainTests(unittest.TestCase):
    def setUp(self):
        self.state = random.getstate()
        random.seed(317)

    def tearDown(self):
        random.setstate(self.state)

    def test_every_band_canvas_size_finishes(self):
        real = common.randint
        for task, first_values in (
            (task_e21a174a, range(7, 14)), (task_e74e1818, range(3, 8))
        ):
            for size in first_values:
                first = True

                def choose(low, high):
                    nonlocal first
                    if first:
                        first = False
                        return size
                    return real(low, high)

                with self.subTest(task=task.__name__, size=size):
                    with patch.object(common, "randint", side_effect=choose):
                        pair = call(task.generate, seconds=5)
                    for canvas in pair.values():
                        grid(canvas)
                    self.assertTrue(all(any(row) for row in pair["input"][1:-1]))

    def test_band_retry_keeps_original_palette(self):
        # Force rejection of the first complete scene. The former generator
        # then iterated flattened pixel colours with the short lengths list.
        real = common.diagonally_connected
        rejected = False

        def connected(pixels):
            nonlocal rejected
            if not rejected and max(r for r, c in pixels) >= 6:
                rejected = True
                return False
            return real(pixels)

        real_int = common.randint
        count = 0

        def dimensions(low, high):
            nonlocal count
            count += 1
            return 13 if count <= 2 else real_int(low, high)

        with patch.object(common, "diagonally_connected", side_effect=connected):
            with patch.object(common, "randint", side_effect=dimensions):
                pair = call(task_e21a174a.generate, seconds=5)
        self.assertTrue(rejected)
        self.assertEqual(len(pair["input"]), 13)
        self.assertEqual(len(pair["output"]), 13)

    def test_previous_oversized_sampling_seeds(self):
        for task, seed in (
            (task_d749d46f, 236726759229235),
            (task_e6721834, 244196699662491),
        ):
            random.seed(seed)
            for _ in range(4):
                for canvas in call(task.generate, seconds=5).values():
                    grid(canvas)

    def test_different_marker_covers_are_rejected(self):
        shapes = [(2, 2, [(0, 0, 3)]), (3, 2, [(0, 0, 3)])]
        self.assertFalse(task_e6721834._unique_placement(
            12, 12, shapes, {(3, 3): 3}))

    def test_marker_colours_disambiguate_omitted_shape(self):
        shapes = [(2, 2, [(0, 0, 3)]), (3, 2, [(0, 0, 6)])]
        self.assertTrue(task_e6721834._unique_placement(
            12, 12, shapes, {(3, 3): 3}))

    def test_identical_painting_from_swapped_shapes_is_allowed(self):
        shapes = [(2, 2, [(0, 0, 3)]), (2, 2, [(0, 0, 3)])]
        self.assertTrue(task_e6721834._unique_placement(
            12, 12, shapes, {(2, 2): 3, (7, 7): 3}))

    def test_hidden_marker_under_body_is_rejected(self):
        self.assertFalse(task_e6721834._unique_placement(
            12, 12, [(3, 3, [(0, 0, 3)])], {(3, 3): 3, (4, 4): 3}))

    def test_search_budget_fails_closed(self):
        self.assertFalse(task_e6721834._unique_placement(
            12, 12, [(2, 2, [(0, 0, 3)])], {(3, 3): 3}, max_states=1))

    def test_original_fixtures_unchanged(self):
        digests = {
            "e21a174a": "2f792dcedb2deb64354ee129002a04de3c9df2192c437c456043963d5b816177",
            "e74e1818": "2416fa9805980abe91222f1df6ce36772b893647b958ca92fd76dd538ff62d21",
            "d749d46f": "2c19ad1ef5749f5f6b78607238821c14653c7f9e7395c8b5aef76378a8927f41",
            "e6721834": "d01bd1743b3e66fa8d1a45708af1205110da7f689282cd1ab1fc76caaff78ad1",
        }
        for task, digest in digests.items():
            fixtures = importlib.import_module("tasks.task_" + task).validate()
            actual = hashlib.sha256(json.dumps(fixtures, sort_keys=True).encode()).hexdigest()
            self.assertEqual(actual, digest)


if __name__ == "__main__":
    unittest.main()

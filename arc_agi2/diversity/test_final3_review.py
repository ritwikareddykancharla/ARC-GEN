"""Focused checks for the 0b148d64 / 1b2d62fb / de1cd16c semantic review.

These pin the diagnosis. The archived checker, not the native constructor, blocks
recertification, and the committed factories are unchanged. They do not certify
anything.
"""

import hashlib
import importlib
import random
import unittest

from ..direct_certificates import certified_factory_source
from ..program_targets import audit_target, verify
from ..runtime import call, grid, reference, solver, verification_solver
from . import final3_review as review
from .recertify import episode

# First recertify index where the archived checker disagrees (factory-independent).
FIRST_BLOCKED = {"0b148d64": (20, 3), "1b2d62fb": (3, 0), "de1cd16c": (16, 1)}


class Final3ReviewTest(unittest.TestCase):
    def test_committed_factories_still_bound(self):
        for tid in review.FAMILIES:
            self.assertIsNotNone(certified_factory_source(tid, 0, list(range(10))), tid)

    def test_minimal_native_counterexamples(self):
        cases = review.minimal_counterexamples()
        for tid, case in cases.items():
            self.assertFalse(case["archived_agrees"], tid)
            self.assertTrue(case["candidate_exact"], tid)
        odd = cases["0b148d64"]["pair"]
        self.assertEqual(odd["output"], [[2] * 8 for _ in range(8)])
        self.assertEqual(len(cases["0b148d64"]["archived_output"]), 15)
        self.assertEqual(cases["1b2d62fb"]["archived_output"], "ValueError('Invalid ARC grid')")
        self.assertEqual(cases["1b2d62fb"]["pair"]["output"], [[0, 0, 0]] * 5)
        self.assertEqual(cases["de1cd16c"]["pair"]["output"], [[3]])
        self.assertEqual(cases["de1cd16c"]["archived_output"], [[4]])

    def test_recertify_first_blocking_pair(self):
        for tid, (index, position) in FIRST_BLOCKED.items():
            module = importlib.import_module("tasks.task_" + tid)
            seed = int(hashlib.sha256(f"diversity-recert:{tid}:{index}".encode())
                       .hexdigest()[:12], 16)
            random.seed(seed)
            pairs = [{k: grid(p[k]) for k in ("input", "output")}
                     for p in [call(module.generate, seconds=3) for _ in range(4)]]
            checker = verification_solver(tid)
            self.assertIs(checker.__code__.co_filename.startswith("reference/"), True)
            pair = pairs[position]
            try:
                archived = grid(checker(pair["input"]))
            except ValueError:
                archived = None
            self.assertNotEqual(archived, pair["output"], tid)
            self.assertEqual(review.run(review.compiled(review.candidate_source(tid)),
                                        pair["input"]), pair["output"], tid)
            # Earlier groups agree, so recertify's stop at this index is exact.
            for earlier in range(index):
                seed = int(hashlib.sha256(f"diversity-recert:{tid}:{earlier}".encode())
                           .hexdigest()[:12], 16)
                random.seed(seed)
                for p in [call(module.generate, seconds=3) for _ in range(4)]:
                    self.assertEqual(grid(checker(grid(p["input"]))), grid(p["output"]))

    def test_candidates_on_canonical_fixture_variants(self):
        for tid in review.FAMILIES:
            fixture = reference(tid)["canonical"]
            for palette in (list(range(10)), review.SECOND_PALETTE):
                for d4 in range(8):
                    source = review.candidate_source(tid, d4, palette)
                    audit_target(tid, source)
                    verify(source, episode(fixture["train"] + fixture["test"], d4, palette))

    def test_archived_solver_is_the_reference_code(self):
        for tid in review.FAMILIES:
            self.assertIn("def transform", reference(tid)["code"])
            self.assertEqual(solver(tid).__code__.co_filename, "reference/" + tid)

    def test_de1cd16c_count_density_ambiguity_is_demonstrated(self):
        found = None
        for four in review.native_groups("de1cd16c", 40):
            info = review.episode_ambiguity("de1cd16c", four)
            if info["distinct_query_predictions"] > 1:
                found = info
                break
        self.assertIsNotNone(found)
        self.assertIn("most_noise (candidate)", found["rivals"]["TRUE"])
        wrong = [v for k, v in found["rivals"].items() if k != "TRUE"]
        self.assertTrue(any("highest_noise_density" in names for names in wrong))


if __name__ == "__main__":
    unittest.main()

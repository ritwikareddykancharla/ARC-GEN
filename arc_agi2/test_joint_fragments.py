"""Regression tests for joint disambiguation rather than first-fragment matching."""
import json
import random
import unittest
from pathlib import Path
from unittest.mock import patch

from . import joint_fragments
from .runtime import grid, solver
from .program_targets import compile_target


class JointFragments(unittest.TestCase):
    def test_saved_greedy_counterexamples_need_global_assignment(self):
        cases = json.loads((Path(__file__).parent / "reports/review-blockers/d6542281.json").read_text())
        source, _ = compile_target("d6542281")
        ns = {}; exec(source, ns)
        old = solver("d6542281")
        for case in cases:
            pair = case["pair"]
            self.assertEqual(joint_fragments.transform(pair["input"]), pair["output"])
            self.assertEqual(grid(ns["solve"]([], pair["input"])), pair["output"])
            try:
                old_result = grid(old(pair["input"]))
            except Exception:
                old_result = None
            self.assertNotEqual(old_result, pair["output"])

    def test_budget_exhaustion_cannot_be_accepted_as_unique(self):
        from tasks import task_d6542281
        pair = task_d6542281.validate()["train"][0]
        with patch.object(joint_fragments, "_NODE_BUDGET", 0):
            with self.assertRaisesRegex(ValueError, "budget"):
                joint_fragments.transform(pair["input"])
        with patch.object(task_d6542281, "_SEARCH_BUDGET", 0):
            with self.assertRaisesRegex(ValueError, "budget"):
                task_d6542281.validate()


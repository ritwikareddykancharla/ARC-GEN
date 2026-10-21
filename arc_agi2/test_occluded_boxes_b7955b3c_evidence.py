"""Focused tests for the b7955b3c direct program and its independent gate."""
import json
import random
import unittest

import numpy as np

from arc_agi2.augmentation import apply_episode
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories.task_b7955b3c import build_program
from arc_agi2.occluded_boxes_b7955b3c_evidence import (
    IntrinsicAmbiguity, readings, require_occluded_boxes_evidence)
from arc_agi2.program_targets import audit_target
from arc_agi2.runtime import call
from tasks import task_b7955b3c as native

ID = list(range(10))
PAL = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
# Hand-built scene accepted by native draw(): background survives only under a plus.
WITNESS = dict(width=16, height=16, wides=[8, 8, 11, 4], talls=[14, 14, 2, 2],
               brows=[0, 0, 14, 14], bcols=[0, 8, 5, 0], bcolors=[0, 1, 2, 3],
               prows=[14, 5], pcols=[4, 11])
# Found by arc_agi2/search_b7955b3c_hard_cases.py: 7 valid readings, all agree.
HARD = dict(width=23, height=8, bgcolor=1, wides=[11, 20, 12], talls=[6, 5, 4],
            brows=[2, 3, 0], bcols=[0, 3, 11], bcolors=[2, 6, 7], prows=[1], pcols=[17])


def program(d4=0, palette=ID):
    src = build_program(d4, palette)
    audit_target('b7955b3c', src)
    ns = {}
    exec(src, ns)
    return ns['solve']


def fixtures():
    data = native.validate()
    return data['train'], data['test']


class FixtureTests(unittest.TestCase):
    def test_all_sixteen_variants(self):
        train, test = fixtures()
        for pal in (ID, PAL):
            for d4 in range(8):
                ds, qs = apply_episode(train, d4, pal), apply_episode(test, d4, pal)
                solve = program(d4, pal)
                for q in qs:
                    require_occluded_boxes_evidence(ds, [{'input': q['input']}], pal)
                for p in ds + qs:
                    self.assertEqual(solve(json.loads(json.dumps(ds)), p['input']), p['output'])

    def test_fixtures_have_single_valid_reading(self):
        train, test = fixtures()
        for p in train + test:
            self.assertEqual(len(readings(p['input'], 8)), 1)


class AmbiguityTests(unittest.TestCase):
    def test_witness_identical_input_different_output(self):
        a = native.generate(bgcolor=4, **WITNESS)
        b = native.generate(bgcolor=5, **WITNESS)
        self.assertIsNotNone(a['input'])
        self.assertEqual(a['input'], b['input'])
        self.assertNotEqual(a['output'], b['output'])
        self.assertFalse(any(4 in row for row in a['input']))

    def test_witness_rival_visible_backgrounds(self):
        a = native.generate(bgcolor=4, **WITNESS)
        res = readings(a['input'], 8)
        self.assertIn(0, res)
        self.assertIn(1, res)
        self.assertNotEqual(int(res[0][15][4]), int(res[1][15][4]))

    def test_solver_and_gate_reject_witness(self):
        train, _ = fixtures()
        a = native.generate(bgcolor=4, **WITNESS)
        with self.assertRaises(ValueError):
            program()(train, a['input'])
        with self.assertRaises(IntrinsicAmbiguity):
            require_occluded_boxes_evidence(train, [{'input': a['input']}], ID)

    def test_hard_identified_case_kept(self):
        train, _ = fixtures()
        p = native.generate(**HARD)
        self.assertIsNotNone(p['input'])
        self.assertGreater(len(readings(p['input'], 8)), 1)
        require_occluded_boxes_evidence(train, [{'input': p['input']}], ID)
        for d4 in range(8):
            for pal in (ID, PAL):
                ds = apply_episode(train, d4, pal)
                q = apply_episode([p], d4, pal)[0]
                self.assertEqual(program(d4, pal)(ds, q['input']), q['output'])


class DemoTests(unittest.TestCase):
    def test_contradicting_demo_not_skipped(self):
        train, test = fixtures()
        bad = json.loads(json.dumps(train))
        bad[0]['output'][0][0] = (bad[0]['output'][0][0] + 1) % 10
        if bad[0]['output'][0][0] == 8:
            bad[0]['output'][0][0] = 0
        with self.assertRaises(ValueError):
            program()(bad, test[0]['input'])
        with self.assertRaises(MissingColourEvidence):
            require_occluded_boxes_evidence(bad, [{'input': test[0]['input']}], ID)

    def test_gate_rederives_plus_colour(self):
        train, test = fixtures()
        with self.assertRaises(MissingColourEvidence):
            require_occluded_boxes_evidence(train, [{'input': test[0]['input']}], PAL)


class AgreementTests(unittest.TestCase):
    def test_program_matches_gate_on_native_samples(self):
        solvers = {}
        for i in range(300):
            random.seed(31310000 + i)
            p = call(native.generate, seconds=5)
            rng = random.Random(i)
            d4 = rng.randrange(8)
            pal = list(range(10)); rng.shuffle(pal)
            q = apply_episode([p], d4, pal)[0]
            res = readings(q['input'], pal[8])
            outs = {o.tobytes() for o in res.values()}
            solve = solvers.setdefault((d4, tuple(pal)), program(d4, pal))
            if len(outs) == 1:
                self.assertEqual(solve([], q['input']), q['output'])
                self.assertTrue(np.array_equal(next(iter(res.values())), q['output']))
            else:
                with self.assertRaises(ValueError):
                    solve([], q['input'])


if __name__ == '__main__':
    unittest.main()

"""Portable tests for the explicitly versioned clearance variant.
Run beside the audited source bundle; no benchmark labels are rewritten.
"""
import copy
import json
import random
import unittest
from pathlib import Path
import hypothesis_core as target
import hypothesis_evidence as gate
import hypothesis_factory as factory
import proposed_constructor as variant
import native
from run_audit import transform
D = Path(__file__).resolve().parent
PAL = list(range(10))
CANONICAL = json.loads((D / 'canonical.json').read_text())

class QueryWithoutAnswer(dict):
    def __getitem__(self, key):
        if key != 'input':
            raise AssertionError('Query access other than input: ' + str(key))
        return super().__getitem__(key)
    def get(self, key, default=None):
        if key != 'input':
            raise AssertionError('Query access other than input: ' + str(key))
        return super().get(key, default)

class HypothesisTests(unittest.TestCase):
    def test_full_parameter_search_and_original_query(self):
        self.assertEqual(len(target.PARAMETERS), 930)
        params = target.fit(CANONICAL['train'])
        self.assertGreater(len(params), 1)
        self.assertEqual(params, gate.fit(CANONICAL['train'], PAL))
        p = CANONICAL['test'][0]
        self.assertEqual(target.solve(CANONICAL['train'], p['input']), p['output'])

    def test_independent_implementation_all_hypotheses(self):
        random.seed(912064)
        p = native.generate()
        g = target._freeze(p['input'])
        initials = gate._initials(g, 0)
        for run, prune in target.PARAMETERS:
            mask = target._prediction(g, run, prune)
            expected = tuple(tuple(3 if mask[r] >> c & 1 else v for c, v in enumerate(row)) for r, row in enumerate(g))
            self.assertEqual(expected, gate._prune(g, initials[run - 1], prune, 0, 3))

    def test_query_answer_never_read(self):
        p = CANONICAL['test'][0]
        gate.require_corridor_evidence(CANONICAL['train'], [QueryWithoutAnswer(input=p['input'])], PAL)
        clean = gate.require_corridor_evidence(CANONICAL['train'], [{'input': p['input']}], PAL)
        poisoned = gate.require_corridor_evidence(CANONICAL['train'], [{'input': p['input'], 'output': [[99]]}], PAL)
        self.assertEqual(clean, poisoned)

    def test_no_default_12_3(self):
        random.seed(926461)
        p = native.generate()
        g = target._freeze(p['input'])
        initials = gate._initials(g, 0)
        altered = [list(row) for row in gate._prune(g, initials[6], 1, 0, 3)]
        demos = [{'input': p['input'], 'output': altered}]
        self.assertIn((7, 1), target.fit(demos))
        self.assertEqual(target.solve(demos, p['input']), altered)

    def test_ambiguous_context_abstains(self):
        # Native seeded query, never selected by comparing its output label.
        random.seed(646110003)
        p = native.generate()
        _, outputs = gate.query_predictions(CANONICAL['train'], p['input'], PAL)
        self.assertGreater(len(outputs), 1)
        with self.assertRaises(ValueError): target.solve(CANONICAL['train'], p['input'])
        with self.assertRaises(gate.MissingColourEvidence):
            gate.require_corridor_evidence(CANONICAL['train'], [{'input': p['input']}], PAL)

    def test_bad_demo_and_no_mutation(self):
        demos = copy.deepcopy(CANONICAL['train'])
        before = copy.deepcopy(demos)
        target.solve(demos, CANONICAL['test'][0]['input'])
        self.assertEqual(demos, before)
        demos[0]['output'] = [[99]]
        with self.assertRaises(ValueError): target.fit(demos)
        with self.assertRaises(gate.MissingColourEvidence): gate.fit(demos, PAL)

    def test_native_inputs_rng_and_fixture_labels_preserved(self):
        random.seed(909)
        before = [native.generate() for _ in range(12)]
        state = random.getstate()
        random.seed(909)
        after = [variant.generate() for _ in range(12)]
        self.assertEqual([p['input'] for p in before], [p['input'] for p in after])
        self.assertEqual(state, random.getstate())
        self.assertEqual(native.validate(), variant.validate())
        self.assertTrue(any(a['output'] != b['output'] for a, b in zip(before, after)))

    def test_canonical_16_d4_palette_variants(self):
        for palette in (PAL, [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]):
            for d4 in range(8):
                ns = {}; exec(factory.build_program(d4, palette), ns)
                demos = [{k: transform(p[k], d4, palette) for k in ('input', 'output')} for p in CANONICAL['train']]
                for p in CANONICAL['train'] + CANONICAL['test']:
                    x, y = transform(p['input'], d4, palette), transform(p['output'], d4, palette)
                    self.assertEqual(ns['solve'](demos, x), y)

if __name__ == '__main__': unittest.main()

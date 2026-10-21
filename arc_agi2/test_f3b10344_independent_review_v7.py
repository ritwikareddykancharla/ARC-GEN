"""Second independent review (v7) tests for f3b10344 same-colour bridges.

Run from the fork root:
  PYTHONPATH=. /Users/ritwika/projects/arc-agi2/.venv/bin/python -m unittest \
      arc_agi2.test_f3b10344_independent_review_v7 -v

What is checked:
1. The canonical train demos contain no uncentred same-colour pair. Rules that bridge any
   overlapping pair therefore fit all three demos but differ on the test (column 25, rows
   15-19). Both the solver and the gate refuse the canonical query under all 16 variants.
2. Adding one native-generated demonstration (proposed context enrichment) identifies the
   query, and the program is exact under all 16 variants.
3. The gate accepts queries=[{'input': grid}] and never reads query outputs. A poisoned
   'output' key changes nothing.
4. Hard boundary-touch cases (trim vs span_any) and uncentred cases are refused when the
   demos lack evidence and answered when they have it. No-survivor and missing bridge colour
   both raise.
5. On seeded native episodes, the gate and the program agree under D4/palette, and the gate
   decision does not depend on D4.
"""
import copy, json, random, unittest
from pathlib import Path
import numpy as np
from arc_agi2.runtime import reference, call
from arc_agi2.fixture_policy import fixture_basis
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories.task_f3b10344 import build_program
from arc_agi2 import centred_bridges_f3b10344_evidence as G
import importlib

native = importlib.import_module('tasks.task_f3b10344')
TID = 'f3b10344'
TASK = reference(TID)['canonical']
EXTRA = json.loads((Path(__file__).resolve().parent / 'f3b10344_proposed_extra_demo.json').read_text())
PALETTES = [list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]]


def program(d4=0, palette=None):
    src = build_program(d4, palette or list(range(10)))
    audit_target(TID, src)
    ns = {'__name__': 'standalone_target'}
    exec(compile(src, '<f3b10344>', 'exec'), ns)
    return src, ns


def tx(pairs, d4, pal):
    return [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in pairs]


def episode(train, test, d4, pal):
    return {'train': tx(train, d4, pal), 'test': [{'input': transformed(p['input'], d4, pal)} for p in test],
            'solutions': [transformed(p['output'], d4, pal) for p in test]}


def boundary_query():
    # A colour-3 box touches only the outer shared row of a colour-2 gap (trim != span_any).
    return native.generate(width=25, height=25, wides=[3, 3, 3, 3, 3], talls=[5, 5, 5, 3, 3],
                           brows=[1, 1, 1, 5, 10], bcols=[1, 12, 20, 7, 7], colors=[2, 2, 2, 3, 3])


def same_colour_boundary_demo():
    return native.generate(width=25, height=25, wides=[3, 3, 3, 3], talls=[5, 5, 3, 3],
                           brows=[5, 5, 3, 12], bcols=[1, 15, 7, 20], colors=[2, 2, 2, 2])


class CanonicalFixture(unittest.TestCase):
    def test_canonical_train_has_no_uncentred_pair_and_overlap_rule_fits(self):
        rule = ('overlap', 'trim_any')
        for p in TASK['train']:
            a = np.asarray(p['input'])
            links = G._links(G.rectangles(a, 0))
            self.assertTrue(all(centred for _, centred, _, _ in links))
            self.assertTrue((G.predict(a, 0, 8, rule) == np.asarray(p['output'])).all())
        q = np.asarray(TASK['test'][0]['input'])
        diff = np.argwhere(G.predict(q, 0, 8, rule) != np.asarray(TASK['test'][0]['output']))
        self.assertEqual(sorted(map(tuple, diff.tolist())), [(r, 25) for r in range(15, 20)])

    def test_canonical_query_refused_by_solver_and_gate_all_variants(self):
        for pal in PALETTES:
            for d4 in range(8):
                src, ns = program(d4, pal)
                ep = episode(TASK['train'], TASK['test'], d4, pal)
                with self.assertRaises(ns['Undetermined']):
                    ns['solve'](copy.deepcopy(ep['train']), ep['test'][0]['input'])
                with self.assertRaises(MissingColourEvidence):
                    G.require_centred_bridge_evidence(ep['train'], queries=[{'input': ep['test'][0]['input']}], palette=pal)
                for d in ep['train']:  # demos are still reproduced exactly
                    self.assertEqual(ns['solve'](copy.deepcopy(ep['train']), d['input']), d['output'])

    def test_enriched_fixture_sixteen_variants(self):
        self.assertEqual(native.generate(**EXTRA['native_params']), EXTRA['pair'])
        train = TASK['train'] + [EXTRA['pair']]
        n = 0
        for pal in PALETTES:
            for d4 in range(8):
                src, _ = program(d4, pal)
                ep = episode(train, TASK['test'], d4, pal)
                G.require_centred_bridge_evidence(ep['train'], queries=[{'input': ep['test'][0]['input']}], palette=pal)
                verify(src, ep); n += 1
        self.assertEqual(n, 16)


class GateInterface(unittest.TestCase):
    def test_live_dispatch_and_labelled_fixture(self):
        from arc_agi2.colour_evidence import require_colour_evidence
        packet = reference(TID)
        basis = fixture_basis(TID, packet)
        self.assertEqual(basis['kind'], 'context_enriched')
        self.assertFalse(basis['original_fixture_context_passed'])
        teaching = packet[basis['fixture']]
        self.assertEqual(teaching['train'][:-1], TASK['train'])
        self.assertEqual(teaching['test'], TASK['test'])
        self.assertEqual(teaching['train'][-1], EXTRA['pair'])
        for pal in PALETTES:
            for d4 in range(8):
                ep = episode(teaching['train'], teaching['test'], d4, pal)
                require_colour_evidence(TID, ep['train'], ep['test'], pal, d4)
                src, _ = program(d4, pal)
                verify(src, ep)


    def test_queries_input_only_and_poisoned_output_ignored(self):
        train = TASK['train'] + [EXTRA['pair']]
        q = TASK['test'][0]['input']
        a = G.require_centred_bridge_evidence(train, queries=[{'input': q}])
        b = G.require_centred_bridge_evidence(train, queries=[{'input': q, 'output': [[5]]}])
        self.assertEqual(a, b)
        self.assertEqual(a['status'], 'identified')

    def test_palette_cross_check_only(self):
        train = TASK['train'] + [EXTRA['pair']]
        with self.assertRaises(MissingColourEvidence):
            G.require_centred_bridge_evidence(train, queries=[{'input': TASK['test'][0]['input']}],
                                              palette=[0, 1, 2, 3, 4, 5, 6, 7, 9, 8])


class HardCases(unittest.TestCase):
    def test_boundary_query_needs_boundary_demo(self):
        q = boundary_query(); demo = same_colour_boundary_demo()
        self.assertIsNotNone(q['input']); self.assertIsNotNone(demo['input'])
        _, ns = program()
        base = TASK['train'] + [EXTRA['pair']]
        with self.assertRaises(ns['Undetermined']):
            ns['solve'](copy.deepcopy(base), q['input'])
        self.assertEqual(G.assess(base, [{'input': q['input']}])['status'], 'context_shortfall')
        full = base + [demo]
        self.assertEqual(ns['solve'](copy.deepcopy(full), q['input']), q['output'])
        self.assertEqual(G.assess(full, [{'input': q['input']}])['status'], 'identified')

    def test_uncentred_demo_alone_refutes_overlap(self):
        _, ns = program()
        self.assertNotEqual(ns['_apply'](EXTRA['pair']['input'], ('overlap', 'trim_any')), EXTRA['pair']['output'])
        self.assertEqual(ns['_apply'](EXTRA['pair']['input'], ('centred', 'trim_any')), EXTRA['pair']['output'])

    def test_no_survivor_raises(self):
        _, ns = program()
        bad = copy.deepcopy(TASK['train']); bad[0]['output'][0][0] = 5
        with self.assertRaises(ns['Undetermined']):
            ns['solve'](bad, TASK['test'][0]['input'])
        self.assertEqual(G.assess(bad, [{'input': TASK['test'][0]['input']}])['status'], 'no_survivor')

    def test_bridge_colour_must_be_demonstrated(self):
        _, ns = program()
        blank = [{'input': [[0] * 5 for _ in range(5)], 'output': [[0] * 5 for _ in range(5)]}]
        # every rival rule bridges this centred, unobstructed pair: only the colour is unknown
        q = [[0] * 10 for _ in range(6)]
        for y in range(1, 4):
            for x in (0, 1, 2, 6, 7, 8):
                q[y][x] = 1
        with self.assertRaises(ns['Undetermined']):
            ns['solve'](blank, q)
        self.assertEqual(G.assess(blank, [{'input': q}])['status'], 'colour_shortfall')
        demo = [{'input': q, 'output': ns['_apply'](q, ('centred', 'trim_any'))}]
        self.assertEqual(G.assess(demo, [{'input': q}])['status'], 'identified')


class NativeAgreement(unittest.TestCase):
    def test_gate_and_program_agree_on_seeded_native_episodes(self):
        rng = random.Random(11); statuses_seen = set()
        for k in range(12):
            random.seed(77000 + k); pairs = []
            while len(pairs) < 4:
                try:
                    pairs.append(call(native.generate, seconds=30))
                except Exception:
                    continue
            pal = list(range(10)); rng.shuffle(pal); per_d4 = set()
            for d4 in range(8):
                t = tx(pairs, d4, pal)
                st = G.assess(t[:3], [{'input': t[3]['input']}])['status']; per_d4.add(st)
                _, ns = program(d4, pal)
                if st == 'identified':
                    self.assertEqual(ns['solve'](copy.deepcopy(t[:3]), t[3]['input']), t[3]['output'])
                else:
                    with self.assertRaises(ns['Undetermined']):
                        ns['solve'](copy.deepcopy(t[:3]), t[3]['input'])
            self.assertEqual(len(per_d4), 1); statuses_seen |= per_d4
        self.assertIn('identified', statuses_seen)


if __name__ == '__main__':
    unittest.main()

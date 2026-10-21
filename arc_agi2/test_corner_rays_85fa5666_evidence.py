"""Portable focused tests for the 85fa5666 direct program and its evidence gate.

Run from the ARC-GEN fork root:
  .venv/bin/python -m unittest -v arc_agi2.test_corner_rays_85fa5666_evidence
"""
import json
import random
import unittest

from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.corner_rays_85fa5666_evidence import (
    READINGS, assess, paint, require_corner_rays_evidence)
from arc_agi2.direct_factories.task_85fa5666 import build_program
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.runtime import reference
from tasks import task_85fa5666 as native

TID = '85fa5666'
ID = list(range(10))
PAL = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
FIX = reference(TID)['canonical']
CONT = (True, False, 'none')          # native random-path reading (d4 = 0)
# Random-path scene with the geometry of fixture pair 2's stopped ray.
W = dict(size=8, brows=[1, 5], bcols=[4, 2], colors=[3, 6, 8, 7, 3, 8, 7, 6])


def solve(d4, pal, demos, q):
    src = build_program(d4, pal)
    audit_target(TID, src)
    ns = {'__name__': 'standalone_target'}
    exec(compile(src, '<t>', 'exec'), ns)
    return ns['solve'](json.loads(json.dumps(demos)), json.loads(json.dumps(q)))


def tf(pairs, d4, pal):
    return [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in pairs]


def differs(g, reading):
    return paint(g, 0, 2, reading) != paint(g, 0, 2, CONT)


def search(pred, seed, limit=20000):
    random.seed(seed)
    for _ in range(limit):
        p = native.generate()
        if pred(p):
            return p
    raise AssertionError('no witness found')


class CornerRays85fa5666(unittest.TestCase):
    def test_fixture_16_variants_gate_called_with_query_inputs_only(self):
        for pal in (ID, PAL):
            for d4 in range(8):
                train = tf(FIX['train'], d4, pal)
                queries = [{'input': transformed(p['input'], d4, pal)} for p in FIX['test']]
                require_corner_rays_evidence(train, queries)               # palette omitted
                require_corner_rays_evidence(train, queries, pal, d4)      # make_record style
                verify(build_program(d4, pal), {
                    'train': train, 'test': queries,
                    'solutions': [transformed(p['output'], d4, pal) for p in FIX['test']]})

    def test_query_label_is_ignored(self):
        q = FIX['test'][0]
        bogus = {'input': q['input'], 'output': [[5] * len(q['input'][0])] * len(q['input'])}
        require_corner_rays_evidence(FIX['train'], [bogus])
        self.assertEqual(assess(FIX['train'], q['input']), assess(FIX['train'], bogus['input']))

    def test_constructor_patch_conflict(self):
        kw = dict(size=12, brows=[1, 5, 8], bcols=[7, 9, 2],
                  colors=[8, 6, 3, 7, 6, 7, 3, 8, 8, 3, 7, 6])
        patched = native.generate(extra_rows=[8, 9], extra_cols=[1, 0], **kw)
        plain = native.generate(**kw)
        self.assertEqual(patched, FIX['train'][1])
        self.assertEqual(patched['input'], plain['input'])
        self.assertEqual([(y, x) for y in range(12) for x in range(12)
                          if patched['output'][y][x] != plain['output'][y][x]], [(8, 1), (9, 0)])

    def test_missing_join_evidence_refused_by_gate_and_program(self):
        demos = [FIX['train'][i] for i in (0, 2, 3)]
        with self.assertRaises(MissingColourEvidence):
            require_corner_rays_evidence(demos, [{'input': FIX['train'][1]['input']}])
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError, 'ambiguous'):
                solve(d4, PAL, tf(demos, d4, PAL), transformed(FIX['train'][1]['input'], d4, PAL))
        w = native.generate(**W)
        with self.assertRaises(MissingColourEvidence):
            require_corner_rays_evidence(demos, [{'input': w['input']}])
        # Fixture demos select the stopping reading, so the answer departs from
        # the native random label exactly at the two stopped cells.
        got = solve(0, ID, FIX['train'], w['input'])
        self.assertEqual([(y, x) for y in range(8) for x in range(8)
                          if got[y][x] != w['output'][y][x]], [(5, 1), (6, 0)])

    def test_obstacle_hard_case_needs_and_uses_evidence(self):
        ob = (True, True, 'none')
        q = search(lambda p: differs(p['input'], ob), 8501)
        ev = search(lambda p: differs(p['input'], ob) and p['input'] != q['input'], 8502)
        joiny = search(lambda p: differs(p['input'], (True, False, 'join'))
                       and differs(p['input'], (True, False, 'graze')), 8503)
        plain = search(lambda p: not any(differs(p['input'], r) for r in READINGS if r[0]), 8504)
        with self.assertRaises(MissingColourEvidence):
            require_corner_rays_evidence([joiny, plain, plain], [{'input': q['input']}])
        demos = [joiny, ev, plain]
        require_corner_rays_evidence(demos, [{'input': q['input']}])
        for pal in (ID, PAL):
            for d4 in range(8):
                require_corner_rays_evidence(tf(demos, d4, pal), [{'input': transformed(q['input'], d4, pal)}])
                self.assertEqual(solve(d4, pal, tf(demos, d4, pal), transformed(q['input'], d4, pal)),
                                 transformed(q['output'], d4, pal))

    def test_native_is_continuation_and_program_agrees_with_gate(self):
        random.seed(85856666)
        stats = {'identified': 0, 'ambiguous': 0}
        for index in range(60):
            pairs = [native.generate() for _ in range(4)]
            for p in pairs:
                self.assertEqual(paint(p['input'], 0, 2, CONT), p['output'])
            pal = list(range(10)); random.Random(index).shuffle(pal)
            status = assess(pairs[:3], pairs[3]['input'])['status']
            stats[status] += 1
            for d4 in (0, 5):
                demos = tf(pairs[:3], d4, pal); q = transformed(pairs[3]['input'], d4, pal)
                if status == 'identified':
                    require_corner_rays_evidence(demos, [{'input': q}])
                    self.assertEqual(solve(d4, pal, demos, q), transformed(pairs[3]['output'], d4, pal))
                else:
                    with self.assertRaises(MissingColourEvidence):
                        require_corner_rays_evidence(demos, [{'input': q}])
                    with self.assertRaisesRegex(ValueError, 'ambiguous'):
                        solve(d4, pal, demos, q)
        self.assertGreater(stats['identified'], 40)

    def test_no_survivor_raises(self):
        bad = json.loads(json.dumps(FIX['train']))
        bad[2]['output'][0][0] = 5
        with self.assertRaises(MissingColourEvidence):
            require_corner_rays_evidence(bad, [{'input': FIX['test'][0]['input']}])
        with self.assertRaisesRegex(ValueError, 'no reading'):
            solve(0, ID, bad, FIX['test'][0]['input'])


if __name__ == '__main__':
    unittest.main()

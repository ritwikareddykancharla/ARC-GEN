"""Portable integration tests for the 9772c176 direct factory (fork-only paths).

Run from the fork root:
    PYTHONPATH=. python -m unittest arc_agi2.test_9772c176_integration_v10 -v

Covers: hash pins (factory, native constructor, canonical fixture), canonical
fixture under all 8 D4 x 2 palettes, poisoned query output rejected by the
verifier, label-free solving (solve never receives labels; poisoning labels
cannot change its answer), d4-independence of the emitted source, demos on
the wrong cap axis raise rather than guess, and a small fresh native sample.
"""
import copy
import hashlib
import inspect
import json
import random
import unittest
from pathlib import Path

from arc_agi2.augmentation import transformed
from arc_agi2.direct_factories import task_9772c176 as factory
from arc_agi2.fixture_policy import digest, fixture_basis
from arc_agi2.program_targets import TargetError, audit_target, verify
from arc_agi2.runtime import reference
from tasks import task_9772c176 as native

TID = '9772c176'
FORK = Path(__file__).resolve().parents[1]
FACTORY_SHA = 'fbf24129a496744a802b52c1b6819a3d6e8f314ec5605b82179b8e91f61c8297'
NATIVE_SHA = '9f90c0054eb9393617df788cce8730cf4c2f04a32301394bb97b878716b8b70f'
CANONICAL_DIGEST = 'fd24427a4ff04325391107a2349b9ac1d5472519c21bba66fb1a00c950a04970'
PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def program(d4, pal):
    src = factory.build_program(d4, pal)
    audit_target(TID, src)
    ns = {}
    exec(src, ns)
    return src, ns


def episode(task, d4, pal):
    return {'train': [{k: transformed(p[k], d4, pal) for k in ('input', 'output')}
                      for p in task['train']],
            'test': [{'input': transformed(p['input'], d4, pal)} for p in task['test']],
            'solutions': [transformed(p['output'], d4, pal) for p in task['test']]}


def poison(g, pal):
    """Flip one cell to a different palette colour (bg <-> roof)."""
    g = copy.deepcopy(g)
    g[0][0] = pal[4] if g[0][0] != pal[4] else pal[0]
    return g


class HashPins(unittest.TestCase):
    def test_sources_pinned(self):
        self.assertEqual(sha(FORK / 'arc_agi2/direct_factories/task_9772c176.py'), FACTORY_SHA)
        self.assertEqual(sha(FORK / 'tasks/task_9772c176.py'), NATIVE_SHA)

    def test_canonical_fixture_immutable(self):
        self.assertEqual(fixture_basis(TID), {'fixture': 'canonical', 'corrected': False})
        self.assertEqual(digest(reference(TID)['canonical']), CANONICAL_DIGEST)


class CanonicalFixture(unittest.TestCase):
    def test_all_d4_two_palettes(self):
        task = reference(TID)[fixture_basis(TID)['fixture']]
        for pal in PALETTES:
            for d4 in range(8):
                src, _ = program(d4, pal)
                self.assertTrue(verify(src, episode(task, d4, pal))['all_exact'])

    def test_poisoned_query_output_rejected(self):
        task = reference(TID)['canonical']
        for pal in PALETTES:
            for d4 in range(8):
                src, _ = program(d4, pal)
                ep = episode(task, d4, pal)
                ep['solutions'] = [poison(s, pal) for s in ep['solutions']]
                with self.assertRaises(TargetError):
                    verify(src, ep)

    def test_answer_independent_of_labels(self):
        # solve() only ever receives demos + query input; poisoning the query
        # label cannot reach it, and removing all demos leaves the answer
        # unchanged (query alone identifies the output).
        self.assertEqual(list(inspect.signature(factory.build_program).parameters), ['d4', 'palette'])
        task = reference(TID)['canonical']
        for pal in PALETTES:
            for d4 in range(8):
                _, ns = program(d4, pal)
                ep = episode(task, d4, pal)
                q = ep['test'][0]['input']
                with_demos = ns['solve'](copy.deepcopy(ep['train']), copy.deepcopy(q))
                no_demos = ns['solve']([], copy.deepcopy(q))
                self.assertEqual(with_demos, ep['solutions'][0])
                self.assertEqual(no_demos, with_demos)

    def test_poisoned_demo_output_raises_not_guesses(self):
        task = reference(TID)['canonical']
        _, ns = program(0, PALETTES[0])
        ep = episode(task, 0, PALETTES[0])
        bad = copy.deepcopy(ep['train'])
        bad[0]['output'] = poison(bad[0]['output'], PALETTES[0])
        with self.assertRaises(ValueError):
            ns['solve'](bad, ep['test'][0]['input'])

    def test_wrong_axis_demos_raise(self):
        # Demos transposed relative to the query admit only the other axis;
        # if that axis cannot explain them all the solver must raise.
        task = reference(TID)['canonical']
        _, ns = program(0, PALETTES[0])
        demos = [{'input': transformed(p['input'], 0, PALETTES[0]),
                  'output': transformed(p['output'], 0, PALETTES[0])} for p in task['train']]
        mixed = [demos[0], {'input': [list(r) for r in zip(*demos[1]['input'])],
                            'output': [list(r) for r in zip(*demos[1]['output'])]}]
        with self.assertRaises(ValueError):
            ns['solve'](mixed, task['test'][0]['input'])


class Source(unittest.TestCase):
    def test_d4_independent_and_label_free(self):
        for pal in PALETTES:
            srcs = {factory.build_program(d4, pal) for d4 in range(8)}
            self.assertEqual(len(srcs), 1)
        src = factory.build_program(0, list(range(10)))
        for banned in ('solutions', 'open(', 'import ', 'd4'):
            self.assertNotIn(banned, src)


class FreshNative(unittest.TestCase):
    def test_fresh_episodes_all_d4(self):
        for k in range(12):
            random.seed(97_720 + k)
            pairs = [native.generate() for _ in range(4)]
            pal = list(range(10))
            random.Random(k).shuffle(pal)
            base = {'train': pairs[:3], 'test': [{'input': pairs[3]['input']}]}
            for d4 in range(8):
                src, _ = program(d4, pal)
                ep = {'train': [{x: transformed(p[x], d4, pal) for x in ('input', 'output')}
                                for p in base['train']],
                      'test': [{'input': transformed(pairs[3]['input'], d4, pal)}],
                      'solutions': [transformed(pairs[3]['output'], d4, pal)]}
                self.assertTrue(verify(src, ep)['all_exact'])


if __name__ == '__main__':
    unittest.main()

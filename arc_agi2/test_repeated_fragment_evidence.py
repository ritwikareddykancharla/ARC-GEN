"""Focused tests for the b230c067 direct factory and independent gate.

Run: PYTHONPATH=/Users/ritwika/projects/ARC-GEN .venv/bin/python test_b230c067.py
"""
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORK = HERE.parent
from arc_agi2.runtime import reference, call
from arc_agi2.fixture_policy import fixture_basis
from arc_agi2.program_targets import audit_target, verify, TargetError
from arc_agi2.augmentation import transformed
from arc_agi2 import repeated_fragment_evidence as G

TID = 'b230c067'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


from arc_agi2.direct_factories.task_b230c067 import build_program as factory
native = load(FORK / 'tasks' / f'task_{TID}.py', 'gen_' + TID)
PALS = [list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]]


def aug_episode(train, query, d4, pal):
    return {'train': [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in train],
            'test': [{'input': transformed(query['input'], d4, pal)}],
            'solutions': [transformed(query['output'], d4, pal)]}


def run(src, ep):
    ns = {'__name__': 'standalone_target'}
    exec(compile(src, '<t>', 'exec'), ns)
    return ns['solve'](json.loads(json.dumps(ep['train'])), ep['test'][0]['input'])


# Hard identifiable scene from the native constructor with explicit args:
# creature {(0,0),(0,1),(1,1),(2,1),(3,1),(3,2)} (w=3, h=4, 6 pixels = w*h//2),
# badcol=1 -> derived sprite {(0,0),(3,1)}: two identical single pixels.
T = [(0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (3, 2)]
D = [(r, c if c < 1 else c - 1) for r, c in T if c != 1]


def hard_pair(brows, bcols):
    import common
    assert not common.overlaps(brows, bcols, [3, 3, 2], [4, 4, 4], 1)
    rows = [p[0] for p in T] + [p[0] for p in D]
    cols = [p[1] for p in T] + [p[1] for p in D]
    idxs = [0] * len(T) + [1] * len(D)
    return native.generate(rows=rows, cols=cols, idxs=idxs, brows=brows, bcols=bcols, bidxs=[0, 0, 1])


def test_fixture_16():
    task = reference(TID)[fixture_basis(TID)['fixture']]
    n = 0
    for pal in PALS:
        for d4 in range(8):
            src = call(factory, d4, pal)
            audit_target(TID, src)
            ep = {'train': [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in task['train']],
                  'test': [{'input': transformed(p['input'], d4, pal)} for p in task['test']],
                  'solutions': [transformed(p['output'], d4, pal) for p in task['test']]}
            verify(src, ep)
            st, _ = G.gate(ep['train'], ep['test'][0]['input'], pal, d4)
            assert st == 'determined', st
            n += 1
    return n


def test_context_shortfall_counterexample():
    task = reference(TID)[fixture_basis(TID)['fixture']]
    query = hard_pair([0, 0, 6], [0, 5, 0])
    # constructor label: fragments red(2); archived reading would make them blue(1)
    assert query['output'][6][0] == 2 and query['output'][9][1] == 2
    raised = 0
    for pal in PALS:
        for d4 in range(8):
            ep = aug_episode(task['train'], query, d4, pal)
            st, info = G.gate(ep['train'], ep['test'][0]['input'], pal, d4)
            assert st == 'context_shortfall', (st, info)
            assert set(info['alive']) == {'constructor', 'all_repeated', 'exactly_twice'}
            try:
                run(factory(d4, pal), ep)
            except ValueError as e:
                assert 'disagree' in str(e)
                raised += 1
    assert raised == 16
    # concrete witness: both readings reproduce all fixture demos, outputs differ
    comps = G.components(query['input'], 0)
    r, _ = G.readings(comps, 1)
    a = G.paint(query['input'], comps, r['constructor'], 1, 2)
    b = G.paint(query['input'], comps, r['all_repeated'], 1, 2)
    assert a == query['output'] and a != b
    return raised


def test_resolved_with_refuting_demo():
    task = reference(TID)[fixture_basis(TID)['fixture']]
    query = hard_pair([0, 0, 6], [0, 5, 0])
    demo = hard_pair([5, 0, 0], [0, 6, 1])
    assert demo['input'] != query['input']
    n = 0
    for pal in PALS:
        for d4 in range(8):
            ep = aug_episode(task['train'][:2] + [demo], query, d4, pal)
            st, info = G.gate(ep['train'], ep['test'][0]['input'], pal, d4)
            assert st == 'determined' and info['alive'] == ['constructor'], (st, info)
            src = factory(d4, pal)
            verify(src, ep)
            n += 1
    return n


def test_wrong_axis_is_rejected():
    # DEL_AXIS matters on the hard resolved episode: the opposite axis must
    # fail loudly (no survivor), never silently pass.
    task = reference(TID)[fixture_basis(TID)['fixture']]
    query = hard_pair([0, 0, 6], [0, 5, 0])
    demo = hard_pair([5, 0, 0], [0, 6, 1])
    bad = 0
    for d4 in range(8):
        pal = PALS[1]
        ep = aug_episode(task['train'][:2] + [demo], query, d4, pal)
        src = factory(d4 + 1 if d4 % 4 != 3 else d4 - 1, pal)  # opposite axis parity
        try:
            verify(src, ep)
        except (TargetError, ValueError):
            bad += 1
    assert bad == 8
    return bad


def test_no_fallback_on_garbage_demo():
    task = reference(TID)[fixture_basis(TID)['fixture']]
    ep = aug_episode(task['train'], task['test'][0], 0, PALS[0])
    ep['train'][0]['output'] = ep['train'][0]['input']  # unexplained demo
    try:
        run(factory(0, PALS[0]), ep)
    except ValueError as e:
        return str(e)
    raise AssertionError('program must not reset to a fallback')


import unittest

class FragmentEvidenceTests(unittest.TestCase):
    def test_original_fixtures(self):self.assertEqual(test_fixture_16(),16)
    def test_ambiguous_context(self):self.assertEqual(test_context_shortfall_counterexample(),16)
    def test_hard_query_retained(self):self.assertEqual(test_resolved_with_refuting_demo(),16)
    def test_axis_consistency(self):self.assertEqual(test_wrong_axis_is_rejected(),8)
    def test_contradictory_demo(self):test_no_fallback_on_garbage_demo()
    def test_shared_gate_ignores_query_output(self):
        from arc_agi2.colour_evidence import require_colour_evidence
        task=reference(TID)['canonical']
        require_colour_evidence(TID,task['train'],[{'input':task['test'][0]['input'],'output':[[9]]}])

if __name__=='__main__':unittest.main()

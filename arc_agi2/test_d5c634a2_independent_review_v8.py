"""Portable focused tests for d5c634a2: the direct factory and the visible gate.

Run: PYTHONPATH=<ARC-GEN fork> python -m pytest arc_agi2/test_d5c634a2_independent_review_v8.py
 or: PYTHONPATH=<ARC-GEN fork> python arc_agi2/test_d5c634a2_independent_review_v8.py
Only fork-relative paths are used.
"""
import importlib.util
import json
from pathlib import Path

from arc_agi2.augmentation import transformed
from arc_agi2.fixture_policy import fixture_basis
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.runtime import reference
from arc_agi2.t_tally_d5c634a2_evidence import (
    MissingTTallyEvidence, cover_tallies, fit_rules, predict, require_t_tally_evidence)

TID = 'd5c634a2'
FORK = Path(__file__).resolve().parents[1]
PALS = [list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NATIVE = _load(FORK / 'tasks' / f'task_{TID}.py', 'native_d5c634a2_v8')
FACTORY = _load(FORK / 'arc_agi2' / 'direct_factories' / f'task_{TID}.py', 'factory_d5c634a2_v8').build_program


def gen(**kw):
    p = NATIVE.generate(**kw)
    assert p['input'] is not None, kw
    return p


def solve_all_frames(p):
    for pal in PALS:
        for d4 in range(8):
            ns = {}
            exec(compile(FACTORY(d4, pal), 'f', 'exec'), ns)
            got = ns['solve']([], transformed(p['input'], d4, pal))
            assert got == transformed(p['output'], d4, pal), (d4, pal)


def raises(fn, reason=None, intrinsic=None):
    try:
        fn()
    except MissingTTallyEvidence as e:
        if reason is not None:
            assert e.reason == reason, e.reason
        if intrinsic is not None:
            assert e.intrinsic == intrinsic
        return e
    raise AssertionError('expected MissingTTallyEvidence')


def fixture():
    return reference(TID)[fixture_basis(TID)['fixture']]


def test_fixture_factory_and_gate_all_frames_with_query_dict_only():
    task = fixture()
    for pal in PALS:
        for d4 in range(8):
            src = FACTORY(d4, pal)
            audit_target(TID, src)
            tr = [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in task['train']]
            qs = [{'input': transformed(p['input'], d4, pal)} for p in task['test']]
            verify(src, {'train': tr, 'test': qs, 'solutions': [transformed(p['output'], d4, pal) for p in task['test']]})
            require_t_tally_evidence(tr, qs)              # no query labels
            require_t_tally_evidence(tr, qs, pal, d4)      # dispatch signature
            for q, p in zip(qs, task['test']):
                assert predict(tr, q['input']) == transformed(p['output'], d4, pal)


def test_gate_never_reads_query_label():
    task = fixture()
    q = {'input': task['test'][0]['input'], 'output': [[7]]}
    require_t_tally_evidence(task['train'], [q])
    assert predict(task['train'], q['input']) == task['test'][0]['output']


def test_association_ambiguity_concrete_counterexample():
    task = fixture()
    demos = [task['train'][0], task['train'][3]]  # tallies (2 up, 2 down) and (1, 1)
    q = gen(width=7, height=7, rows=[1, 4, 6], cols=[1, 4, 1], cdirs=[1, 0, 1])  # (2 up, 1 down)
    _, _, _, _, rules = fit_rules(demos)
    # Concrete counterexample: two demo-consistent rules disagree on the query.
    preds = set()
    for sigma, observed in rules:
        out = [[0] * 6 for _ in range(3)]
        for X in observed:
            n = sum(k for k, s in zip((2, 1, 0, 0), sigma) if s == X)
            for r, c in observed[X].get(n, ()):
                out[r][c] = X
        preds.add(json.dumps(out))
    assert len(preds) >= 2 and json.dumps(q['output']) in preds
    e = raises(lambda: require_t_tally_evidence(demos, [{'input': q['input']}]),
               'orientation_colour_association_unobserved', intrinsic=False)
    # Equal-count query: the association does not matter, so the gate passes.
    eq = task['train'][0]
    assert predict(demos, eq['input']) == eq['output']
    # One unequal demo pins the association.
    pinned = demos + [task['train'][4]]  # (1 up, 2 down)
    assert predict(pinned, q['input']) == q['output']


def test_each_tally_prefix_needs_visible_evidence():
    task = fixture()
    demos = [task['train'][3], task['train'][0], task['train'][4]]  # up in {1,2}; down in {1,2}
    q = task['train'][2]  # 4 up, 1 down
    raises(lambda: require_t_tally_evidence(demos, [{'input': q['input']}]),
           'tally_prefix_4_unobserved', intrinsic=False)
    assert predict(demos + [task['train'][5]] + [task['train'][2]], q['input']) == q['output']
    # Down prefix 3 is unobserved here even though up 3 is observed.
    demos2 = [task['train'][5], task['train'][4]]  # (3 up, 1 down), (1 up, 2 down)
    q2 = task['train'][1]  # (1 up, 3 down)
    raises(lambda: predict(demos2, q2["input"]), intrinsic=False)


def test_touching_and_shared_cell_border_bars():
    cases = [
        dict(width=7, height=5, rows=[0, 0, 4], cols=[1, 4, 3], cdirs=[0, 0, 1]),   # touching on row 0
        dict(width=7, height=5, rows=[0, 0, 4], cols=[2, 4, 1], cdirs=[0, 0, 1]),   # shared cell on row 0
        dict(width=8, height=6, rows=[5, 5, 0], cols=[2, 4, 4], cdirs=[1, 1, 0]),   # shared cell on bottom row
        dict(width=13, height=5, rows=[0, 0, 0, 4, 4], cols=[1, 3, 6, 2, 5], cdirs=[0, 0, 0, 1, 1]),  # 3 bars touching/sharing
        dict(width=10, height=4, rows=[3, 3, 3, 0], cols=[1, 4, 6, 7], cdirs=[1, 1, 1, 0]),
    ]
    for kw in cases:
        p = gen(**kw)
        top_or_bottom = [p['input'][0], p['input'][-1]]
        assert any(sum(1 for v in row if v) > 3 for row in top_or_bottom), kw
        u, d = kw['cdirs'].count(1), kw['cdirs'].count(0)
        assert cover_tallies(p['input'], 0) == {(u, d, 0, 0)}, kw
        solve_all_frames(p)


def test_native_hidden_duplicate_witness_is_invisible():
    a = dict(width=4, height=14, rows=[1, 9, 13, 13], cols=[1, 1, 2, 2], cdirs=[0, 1, 1, 1])
    b = dict(width=4, height=14, rows=[1, 9, 13, 1], cols=[1, 1, 2, 1], cdirs=[0, 1, 1, 0])
    pa, pb = gen(**a), gen(**b)
    assert pa['input'] == pb['input'] and pa['output'] != pb['output']
    # The visible parse sees 2 up and 1 down; both latents hold a duplicate.
    assert cover_tallies(pa['input'], 0) == {(2, 1, 0, 0)}
    for kw in (a, b):
        assert len(set(zip(kw['rows'], kw['cols'], kw['cdirs']))) < len(kw['cdirs'])


def test_unseen_direction_is_not_defaulted():
    task = fixture()
    demos = task['train']
    q = transformed(task['test'][0]['input'], 1, list(range(10)))  # stems now horizontal
    raises(lambda: predict(demos, q), intrinsic=False)


def test_foreign_colour_query_is_intrinsic():
    task = fixture()
    q = [row[:] for row in task['test'][0]['input']]
    q[0][0] = 5
    raises(lambda: predict(task['train'], q), 'query_colours_outside_demo_context', intrinsic=True)


def test_gate_decision_is_frame_invariant():
    task = fixture()
    for split in range(len(task['train'])):
        demos = task['train'][:split] + task['train'][split + 1:]
        q = task['train'][split]
        outcomes = set()
        for pal in PALS:
            for d4 in range(8):
                tr = [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in demos]
                try:
                    got = predict(tr, transformed(q['input'], d4, pal))
                    assert got == transformed(q['output'], d4, pal)
                    outcomes.add('ok')
                except MissingTTallyEvidence as e:
                    outcomes.add(e.reason)
        assert len(outcomes) == 1, (split, outcomes)


if __name__ == '__main__':
    names = [n for n in sorted(globals()) if n.startswith('test_')]
    for n in names:
        globals()[n]()
        print('ok', n)
    print(json.dumps({'passed': len(names)}))

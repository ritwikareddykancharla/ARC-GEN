"""Portable integration tests for d5c634a2 (v10, final integration prep).

Run: PYTHONPATH=<ARC-GEN fork> python -m pytest arc_agi2/test_d5c634a2_integration_v10.py
 or: PYTHONPATH=<ARC-GEN fork> python arc_agi2/test_d5c634a2_integration_v10.py
The tests use only fork-relative paths and never write to the fork.

Covers:
  * hash pins for the factory, the gate and the native constructor. The
    native file may be the LIVE one or the PROPOSED patch, and nothing else.
  * the production gate under a query label-access trap: a query mapping
    that raises on every key except 'input', and also on iteration,
    len, items, values and copy.
  * that the gate result does not depend on the query label: the same
    decision with no label, a poisoned label or the true label, under 8 D4
    x 2 palettes. verify() rejects the poisoned label, so the verifier is
    the only consumer of labels.
  * the proposed constructor fix, derived in memory from the live source:
    its sha equals the pinned proposal, validate() is byte-identical, and
    no sampled pair has a hidden duplicate. Every sampled pair is
    factory-exact with a unique visible parse equal to the label.
  * the dispatch snippet root would add, run on an in-memory copy of
    colour_evidence; the shared file is left untouched.
"""
import hashlib
import importlib.util
import json
import random
import sys
import types
from pathlib import Path

from arc_agi2.augmentation import transformed
from arc_agi2.fixture_policy import fixture_basis
from arc_agi2.program_targets import TargetError, audit_target, verify
from arc_agi2.runtime import reference
from arc_agi2.t_tally_d5c634a2_evidence import (
    MissingTTallyEvidence, cover_tallies, predict, require_t_tally_evidence)

TID = 'd5c634a2'
FORK = Path(__file__).resolve().parents[1]
NATIVE_PATH = FORK / 'tasks' / f'task_{TID}.py'
FACTORY_PATH = FORK / 'arc_agi2' / 'direct_factories' / f'task_{TID}.py'
GATE_PATH = FORK / 'arc_agi2' / 't_tally_d5c634a2_evidence.py'
PINS = {
    'factory': '7889f3129f3eef90574126600fa30be1423350815f9a1b364786ec323496060d',
    'gate': '35dfcc585c5a1c210c7189dfc74bf9bc694dc0cfe740be1180103baed1357c04',
    'native_live': 'ae4815e88a27242fb6e08e91429d78f071dcf63f71c2f5b972ffc70ba4d1e04d',
    'native_proposed': 'd15fb53f8087e521da2f26f8f818dc564c462041924dc69ebb7b040627ae1d29',
    # Root-applied variant seen 2026-10-21 06:01: same reject line, different
    # comment, original docstring. Semantically equal to native_proposed.
    'native_root_applied': '3cf515b79b114b5be10e62a1565cd698470ad43e759ab6b898d0cac7970bc841',
    # sha256 of the proposal with comment lines and the docstring line dropped.
    'native_proposed_semantic': 'dc794a35c6922b9d530c42188945439c8d3c0aa613c7f1278dbdf3b56720db4d',
}
REJECT = '      if len(set(zip(rows, cols, cdirs))) < len(cdirs): continue\n'
PALS = [list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]]
OLD_DOC = '"""Generator."""\n'
NEW_DOC = '"""Generator (PROPOSED: rejects invisible duplicate T placements; not live native)."""\n'
ANCHOR = '      cols = [common.randint(1, width - 2) for _ in cdirs]\n'
INSERT = (
    '      # PROPOSED FIX (host review): an exact duplicate (row, col, cdir) is\n'
    '      # invisible in the input (same cells, ids overwritten so the adjacency\n'
    '      # check passes) but cdirs.count() still tallies it in the output.\n'
    '      if len(set(zip(rows, cols, cdirs))) < len(cdirs): continue\n')


def sha(path_or_text):
    data = path_or_text.read_bytes() if isinstance(path_or_text, Path) else path_or_text.encode()
    return hashlib.sha256(data).hexdigest()


def module_from_source(src, name):
    m = types.ModuleType(name)
    exec(compile(src, name, 'exec'), m.__dict__)
    return m


def semantic(src):
    """Drop comment lines and the module docstring line."""
    return [ln for ln in src.splitlines()
            if not ln.lstrip().startswith('#') and not ln.startswith('"""Generator')]


def semantic_sha(src):
    return sha('\n'.join(semantic(src)))


def live_is_fixed():
    return REJECT in NATIVE_PATH.read_text()


def constructor_source():
    """Constructor under test: the live file if it already holds the fix,
    else the pinned proposal derived in memory from the unpatched live file."""
    live = NATIVE_PATH.read_text()
    if live_is_fixed():
        return live
    assert sha(NATIVE_PATH) == PINS['native_live']
    assert live.count(OLD_DOC) == 1 and live.count(ANCHOR) == 1
    return live.replace(OLD_DOC, NEW_DOC).replace(ANCHOR, ANCHOR + INSERT)


def load_factory():
    spec = importlib.util.spec_from_file_location('factory_d5c634a2_v10', FACTORY_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.build_program


FACTORY = load_factory()


def fixture():
    return reference(TID)[fixture_basis(TID)['fixture']]


class LabelTrap(dict):
    """Query mapping that allows only ['input'] and .get('input')."""

    def __getitem__(self, k):
        if k != 'input':
            raise AssertionError('gate accessed query key %r' % (k,))
        return dict.__getitem__(self, k)

    def get(self, k, default=None):
        if k != 'input':
            raise AssertionError('gate accessed query key %r via get' % (k,))
        return dict.get(self, k, default)

    def _deny(self, *a, **k):
        raise AssertionError('gate enumerated the query mapping')

    __iter__ = keys = items = values = copy = __len__ = __contains__ = _deny


def trap(inp, label):
    q = LabelTrap()
    dict.__setitem__(q, 'input', inp)
    dict.__setitem__(q, 'output', label)
    return q


def frames():
    for pal in PALS:
        for d4 in range(8):
            yield d4, pal


def tframe(task, d4, pal):
    tr = [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in task['train']]
    qi = [transformed(p['input'], d4, pal) for p in task['test']]
    qo = [transformed(p['output'], d4, pal) for p in task['test']]
    return tr, qi, qo


def gate_outcome(demos, queries):
    try:
        require_t_tally_evidence(demos, queries)
        return 'ok'
    except MissingTTallyEvidence as e:
        return e.reason


def poison(grid):
    g = [row[:] for row in grid]
    g[1][1] = next(v for v in range(10) if v != g[1][1])
    return g


def test_hash_pins():
    assert sha(FACTORY_PATH) == PINS['factory']
    assert sha(GATE_PATH) == PINS['gate']
    assert sha(NATIVE_PATH) in (PINS['native_live'], PINS['native_proposed'], PINS['native_root_applied'])
    src = constructor_source()
    if not live_is_fixed():
        assert sha(src) == PINS['native_proposed']  # in-memory derivation is exact
    # Live or derived, the constructor equals the proposal up to comments/docstring.
    assert semantic_sha(src) == PINS['native_proposed_semantic']


def test_canonical_fixture_factory_exact_and_gate_trap_all_frames():
    task = fixture()
    for d4, pal in frames():
        src = FACTORY(d4, pal)
        audit_target(TID, src)
        tr, qi, qo = tframe(task, d4, pal)
        verify(src, {'train': tr, 'test': [{'input': x} for x in qi], 'solutions': qo})
        # Production entry: make_record passes episode['test'] (may hold outputs).
        require_t_tally_evidence(tr, [trap(x, y) for x, y in zip(qi, qo)], pal, d4)
        for x, y in zip(qi, qo):
            assert predict(tr, x) == y


def test_poisoned_query_label_changes_verify_but_not_gate():
    task = fixture()
    for d4, pal in frames():
        src = FACTORY(d4, pal)
        tr, qi, qo = tframe(task, d4, pal)
        bad = [poison(y) for y in qo]
        outcomes = {gate_outcome(tr, [trap(x, y) for x, y in zip(qi, labels)])
                    for labels in (qo, bad, [[[7]]] * len(qi))}
        outcomes.add(gate_outcome(tr, [{'input': x} for x in qi]))
        assert outcomes == {'ok'}, outcomes
        try:
            verify(src, {'train': tr, 'test': [{'input': x} for x in qi], 'solutions': bad})
        except TargetError:
            pass
        else:
            raise AssertionError('verify accepted a poisoned query label')


def test_gate_rejection_is_label_independent_under_trap():
    """Leave-one-out over fixture pairs: every reject and every accept is
    the same whatever query label sits behind the trap."""
    task = fixture()
    pairs = task['train'] + task['test']
    seen = set()
    for i, q in enumerate(pairs):
        demos = [p for j, p in enumerate(pairs) if j != i][:3]
        for d4, pal in list(frames())[::5]:
            tr = [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in demos]
            x, y = transformed(q['input'], d4, pal), transformed(q['output'], d4, pal)
            outs = {gate_outcome(tr, [trap(x, lab)]) for lab in (y, poison(y), [[0]])}
            outs.add(gate_outcome(tr, [{'input': x}]))
            assert len(outs) == 1, (i, d4, outs)
            seen |= outs
    assert 'ok' in seen and len(seen) >= 2, seen  # both accepts and rejects exercised


def test_fixed_constructor_validate_equals_fixture_and_no_hidden_duplicates():
    sys.path.insert(0, str(FORK))
    prop = module_from_source(constructor_source(), 'native_proposed_d5c634a2_v10')
    fx = fixture()
    pv = prop.validate()
    assert [p['input'] for p in pv['train'] + pv['test']] == [p['input'] for p in fx['train'] + fx['test']]
    assert [p['output'] for p in pv['train'] + pv['test']] == [p['output'] for p in fx['train'] + fx['test']]
    state = random.getstate()
    try:
        merged = 0
        for i in range(200):
            seed = int(hashlib.sha256(f'd5c634a2-v10:{i}'.encode()).hexdigest()[:12], 16)
            random.seed(seed)
            p = prop.generate()
            d4, pal = i % 8, PALS[i % 2]
            ns = {}
            exec(compile(FACTORY(d4, pal), 'f', 'exec'), ns)
            assert ns['solve']([], transformed(p['input'], d4, pal)) == transformed(p['output'], d4, pal), seed
            t = cover_tallies(p['input'], 0)
            assert len(t) == 1, seed
            up, down = next(iter(t))[:2]
            out = p['output']
            assert sum(v == 3 for r in out for v in r) == up and sum(v == 1 for r in out for v in r) == down
            merged += any(sum(1 for v in row if v) > 3 for row in (p['input'][0], p['input'][-1]))
        assert merged > 0  # touching/shared-cell border bars kept (no narrowing)
    finally:
        random.setstate(state)


def test_live_native_defect_witness_still_reproduces_or_is_fixed():
    sys.path.insert(0, str(FORK))
    native = module_from_source(NATIVE_PATH.read_text(), 'native_now_d5c634a2_v10')
    a = dict(width=4, height=14, rows=[1, 9, 13, 13], cols=[1, 1, 2, 2], cdirs=[0, 1, 1, 1])
    b = dict(width=4, height=14, rows=[1, 9, 13, 1], cols=[1, 1, 2, 1], cdirs=[0, 1, 1, 0])
    pa, pb = native.generate(**a), native.generate(**b)
    # Explicit latents bypass the random-branch filter in both versions.
    assert pa['input'] == pb['input'] and pa['output'] != pb['output']
    assert cover_tallies(pa['input'], 0) == {(2, 1, 0, 0)}


def test_dispatch_live_or_in_memory_copy():
    """Use the live dispatch if it is already wired for d5c634a2. Otherwise
    exec the snippet root would add on an in-memory copy of colour_evidence."""
    import arc_agi2.colour_evidence as ce
    src = Path(ce.__file__).read_text()
    head = 'def require_colour_evidence(task_id, demonstrations, queries, palette=None, d4=0):\n'
    assert src.count(head) == 1
    if "task_id == 'd5c634a2'" in src:
        patched = ce
        run_dispatch(patched, ce)
        return
    snippet = ("    if task_id == 'd5c634a2':\n"
               "        from arc_agi2.t_tally_d5c634a2_evidence import require_t_tally_evidence\n"
               "        require_t_tally_evidence(demonstrations, queries, palette, d4)\n"
               "        return\n")
    patched = module_from_source(src.replace(head, head + snippet), 'colour_evidence_d5c634a2_v10')
    run_dispatch(patched, ce)


def run_dispatch(patched, ce):
    task = fixture()
    for d4, pal in frames():
        tr, qi, qo = tframe(task, d4, pal)
        patched.require_colour_evidence(TID, tr, [trap(x, y) for x, y in zip(qi, qo)], pal, d4)
    try:
        patched.require_colour_evidence(TID, task['train'][:1], [{'input': task['train'][2]['input']}])
    except ce.MissingColourEvidence:
        pass  # the gate's exception class is the production MissingColourEvidence
    else:
        raise AssertionError('thin context accepted')


def test_label_trap_negative_control():
    """The trap must fire on any label access a leaky gate could make."""
    q = trap([[0]], [[1]])
    probes = [lambda: q['output'], lambda: q.get('output'), lambda: list(q),
              lambda: dict(q.items()), lambda: 'output' in q, lambda: len(q), lambda: q.copy()]
    for probe in probes:
        try:
            probe()
        except AssertionError:
            continue
        raise AssertionError('trap missed a label access')
    assert q['input'] == [[0]] and q.get('input') == [[0]]


def test_production_make_record_path():
    """compile_target resolves this factory. make_record admits the
    canonical fixture in all 16 frames, rejects poisoned solutions only
    inside verify, and rejects a thin context at the gate."""
    from arc_agi2.program_targets import compile_target, make_record
    task = fixture()
    for d4, pal in frames():
        tr, qi, qo = tframe(task, d4, pal)
        src, _ = compile_target(TID, d4, pal)
        assert src == FACTORY(d4, pal)
        ep = {'episode_id': 'v10-%d' % d4, 'task_id': TID, 'train': tr, 'test': [{'input': x} for x in qi],
              'solutions': qo, 'color_permutation': pal, 'd4_transform': d4}
        make_record(ep)
        try:
            make_record(dict(ep, solutions=[poison(y) for y in qo]))
        except TargetError:
            pass
        else:
            raise AssertionError('poisoned solutions admitted')
    thin = {'episode_id': 'thin', 'task_id': TID, 'train': task['train'][:1],
            'test': [{'input': task['train'][2]['input']}], 'solutions': [task['train'][2]['output']]}
    try:
        make_record(thin)
    except MissingTTallyEvidence as e:
        assert not e.intrinsic
    else:
        raise AssertionError('thin context admitted')


if __name__ == '__main__':
    names = [n for n in sorted(globals()) if n.startswith('test_')]
    for n in names:
        globals()[n]()
        print('ok', n)
    print(json.dumps({'passed': len(names)}))

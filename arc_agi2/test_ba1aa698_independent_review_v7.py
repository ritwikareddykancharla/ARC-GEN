"""Portable focused tests for ba1aa698 (panel motif translation): factory, gate, teaching copy.

Run from the fork root:
  PYTHONPATH=. /Users/ritwika/projects/arc-agi2/.venv/bin/python -m unittest \
      arc_agi2.test_ba1aa698_independent_review_v7 -v

Only fork-relative paths are used. Nothing here edits native tasks or reference labels.

What is checked:
1. Source pins: the factory, the gate and the native constructor match the reviewed SHA256.
2. Canonical fixture conflict (unresolved, root decision). Canonical train pair 2 is
   validate(extra=1). Native seed 15323 generates the identical input with a different
   label. The strict factory raises Inconsistent and the gate refuses, under all 16 variants.
   The canonical fixture itself is unchanged.
3. The proposed teaching copy (ba1aa698_proposed_teaching_fixture.json) differs from
   canonical only in 4 output cells of train[1]. It equals the native generate() with
   extra=0, and the program and gate are exact under all 16 variants via verify().
4. The gate never reads query labels. Queries carry a poisoned 'output' and a trap mapping
   that raises on any key except 'input'. An AST scan also shows that query objects are
   only ever subscripted with 'input'.
5. No demos means ambiguous (context shortfall). A corrupt demo means rejection. A single
   demo identifies ORDER. On seeded native episodes, gate == program == label under
   D4/palette (labels are compared after prediction).
"""
import ast
import hashlib
import importlib.util
import json
import random
import unittest
from collections.abc import Mapping
from pathlib import Path

from arc_agi2.augmentation import transformed
from arc_agi2.fixture_policy import fixture_basis
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.runtime import reference, call

TID = 'ba1aa698'
HERE = Path(__file__).resolve().parent
FORK = HERE.parent
PALS = [list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]]
FACTORY_PATH = HERE / 'direct_factories' / f'task_{TID}.py'
GATE_PATH = HERE / 'panel_motion_ba1aa698_evidence.py'
NATIVE_PATH = FORK / 'tasks' / f'task_{TID}.py'
TEACHING_PATH = HERE / 'ba1aa698_proposed_teaching_fixture.json'
PINS = {
    'factory': 'd9c288d58049ac7d6ca6b663a4ab6d626140469ed3eeec63211117fea39b2c32',
    'gate': '0aa46fc6fa3b9e63abf74b107a59fdcb949f81f7f46303b6449cfc6f10aef476',
    'native': '8f3909440a766e9fabd1ed73141da9bf0c6f081ccdf2974f3222bcf544a4a2c6',
}
CANONICAL_DIGEST = '6dc2d46cc712ffc6810b6b7f028852346ae4e5c03bc8f0f69539e8cdd35a531e'
TEACHING_DIGEST = '7c4e28c692223c47602e5b444d81b2f372805e094158ffb8f5bbf63f8715bc0f'


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NATIVE = _load(NATIVE_PATH, 'native_ba1aa698_v7t')
FACTORY = _load(FACTORY_PATH, 'factory_ba1aa698_v7t').build_program
G = _load(GATE_PATH, 'gate_ba1aa698_v7t')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest = lambda o: hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()


def program(d4=0, pal=None):
    src = call(FACTORY, d4, pal or list(range(10)))
    audit_target(TID, src)
    ns = {'__name__': 'standalone_target'}
    exec(compile(src, '<ba1aa698>', 'exec'), ns)
    return src, ns['solve']


def tx(pairs, d4, pal):
    return [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in pairs]


def episode(task, d4, pal):
    return {'train': tx(task['train'], d4, pal),
            'test': [{'input': transformed(p['input'], d4, pal)} for p in task['test']],
            'solutions': [transformed(p['output'], d4, pal) for p in task['test']]}


def raised(fn, *a, **k):
    try:
        fn(*a, **k)
        return None
    except Exception as e:  # noqa: BLE001 - test helper records the exception type
        return type(e).__name__


class QueryTrap(Mapping):
    """Query object exposing only 'input'. Any other key access fails the test."""

    def __init__(self, grid):
        self._g = grid
        self.accessed = []

    def __getitem__(self, k):
        self.accessed.append(k)
        if k != 'input':
            raise AssertionError('gate read query key %r' % (k,))
        return self._g

    def __iter__(self):
        raise AssertionError('gate iterated query keys')

    def __len__(self):
        raise AssertionError('gate took len of query')


def canonical():
    return reference(TID)['canonical']  # conflict tests always inspect immutable originals


def teaching():
    d = json.loads(TEACHING_PATH.read_text())
    return d['metadata'], {'train': d['train'], 'test': d['test']}


class SourcePins(unittest.TestCase):
    def test_hashes(self):
        self.assertEqual(sha(FACTORY_PATH), PINS['factory'])
        self.assertEqual(sha(GATE_PATH), PINS['gate'])
        self.assertEqual(sha(NATIVE_PATH), PINS['native'])

    def test_emitted_source_independent_of_d4_palette_and_audited(self):
        base = program()[0]
        for pal in PALS:
            for d4 in range(8):
                self.assertEqual(program(d4, pal)[0], base)
        tree = ast.parse(base)  # comments are excluded; only code identifiers/imports/strings
        idents = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        idents |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        imports = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
        strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        self.assertEqual(imports, {'numpy'})
        for tok in ('solutions', 'Counter', 'random', 'choice', 'open', 'eval', 'exec'):
            self.assertNotIn(tok, idents)
        self.assertNotIn('solutions', strings)

    def test_gate_has_no_arcgen_imports(self):
        tree = ast.parse(GATE_PATH.read_text())
        mods = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        mods |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(mods, {'numpy'})


class CanonicalConflict(unittest.TestCase):
    def test_canonical_immutable_and_equals_native_validate(self):
        can = canonical()
        self.assertEqual(digest(can), CANONICAL_DIGEST)
        self.assertEqual(NATIVE.validate(), can)

    def test_same_input_conflicting_label(self):
        can = canonical()
        random.seed(15323)
        w = NATIVE.generate()
        self.assertEqual(w['input'], can['train'][1]['input'])
        self.assertNotEqual(w['output'], can['train'][1]['output'])
        self.assertEqual(G.predict(w['input'], 1), w['output'])
        rows = lambda o: sorted({r for r, row in enumerate(o[1:-1], 1) if 8 in row[1:-1]})
        self.assertEqual(rows(w['output']), [11, 12])
        self.assertEqual(rows(can['train'][1]['output']), [12, 13])

    def test_all16_strict_refusal(self):
        can = canonical()
        for pal in PALS:
            for d4 in range(8):
                ep = episode(can, d4, pal)
                _, solve = program(d4, pal)
                self.assertEqual(raised(solve, ep['train'], ep['test'][0]['input']), 'Inconsistent')
                self.assertEqual(raised(G.require_ba1aa698_evidence, ep['train'],
                                        [{'input': ep['test'][0]['input']}]),
                                 'MissingBa1aa698Evidence')
                self.assertEqual(raised(verify, program(d4, pal)[0], ep), 'Inconsistent')

    def test_leave_pair2_out_only_pair2_wrong(self):
        can = canonical()
        demos = [can['train'][0], can['train'][2]]
        _, solve = program()
        exact = []
        for p in can['train'] + can['test']:
            ans = solve(demos, p['input'])
            self.assertEqual(ans, G.require_ba1aa698_evidence(demos, [{'input': p['input']}])[0])
            exact.append(ans == p['output'])
        self.assertEqual(exact, [True, False, True, True])


class TeachingCopy(unittest.TestCase):
    def test_metadata_digests_and_four_cells(self):
        meta, t = teaching()
        can = canonical()
        self.assertEqual(meta['canonical_sha256'], CANONICAL_DIGEST)
        self.assertEqual(digest(t), TEACHING_DIGEST)
        self.assertEqual(meta['teaching_sha256'], TEACHING_DIGEST)
        self.assertEqual(meta['constructor_source_sha256'], PINS['native'])
        self.assertIs(meta['original_benchmark_labels_changed'], False)
        self.assertIs(meta['uncertain_original_intent'], True)
        self.assertEqual(t['test'], can['test'])
        changes = []
        for split in ('train', 'test'):
            for i, (a, b) in enumerate(zip(can[split], t[split])):
                self.assertEqual(a['input'], b['input'])
                for r, row in enumerate(a['output']):
                    for c, v in enumerate(row):
                        if v != b['output'][r][c]:
                            changes.append({'split': split, 'pair_index': i, 'row': r, 'column': c,
                                            'original': v, 'proposed': b['output'][r][c]})
        self.assertEqual(changes, meta['changed_cells'])
        self.assertEqual(len(changes), 4)

    def test_teaching_pair2_is_native_extra0(self):
        _, t = teaching()
        can = canonical()
        p = NATIVE.generate(width=4, frames=3, offset=3, flip=0, colors=[8, 2, 8], pattern=[1, 1, 1, 1])
        self.assertEqual(p, t['train'][1])
        self.assertEqual([t['train'][0], t['train'][2]], [can['train'][0], can['train'][2]])

    def test_teaching_all16_exact(self):
        _, t = teaching()
        for pal in PALS:
            for d4 in range(8):
                ep = episode(t, d4, pal)
                src, solve = program(d4, pal)
                verify(src, ep)
                for p, sol in zip(ep['train'] + ep['test'], [q['output'] for q in ep['train']] + ep['solutions']):
                    pred = solve(ep['train'], p['input'])
                    gate = G.require_ba1aa698_evidence(ep['train'], [QueryTrap(p['input'])])[0]
                    self.assertEqual(pred, gate)
                    self.assertEqual(pred, sol)


class QueryLabelIsolation(unittest.TestCase):
    def test_trap_and_poison(self):
        _, t = teaching()
        for pal in PALS:
            for d4 in range(8):
                ep = episode(t, d4, pal)
                q = ep['test'][0]['input']
                trap = QueryTrap(q)
                a = G.require_ba1aa698_evidence(ep['train'], [trap])
                self.assertEqual(trap.accessed, ['input'])
                poisoned = [{'input': q, 'output': [[9]]}]
                b = G.require_ba1aa698_evidence(ep['train'], poisoned)
                poisoned2 = [{'input': q, 'output': ep['solutions'][0]}]
                c = G.require_ba1aa698_evidence(ep['train'], poisoned2)
                self.assertEqual(a, b)
                self.assertEqual(a, c)
        # The canonical refusal does not change if the query label is poisoned or supplied.
        can = canonical()
        for out in ([[0]], can['test'][0]['output']):
            self.assertEqual(raised(G.require_ba1aa698_evidence, can['train'],
                                    [{'input': can['test'][0]['input'], 'output': out}]),
                             'MissingBa1aa698Evidence')

    def test_ast_queries_only_subscripted_with_input(self):
        tree = ast.parse(GATE_PATH.read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'require_ba1aa698_evidence')
        qnames = {'queries'}
        for n in ast.walk(fn):
            if isinstance(n, ast.For) and isinstance(n.iter, ast.Name) and n.iter.id in qnames:
                qnames.add(n.target.id)
        subs = [n for n in ast.walk(fn) if isinstance(n, ast.Subscript)
                and isinstance(n.value, ast.Name) and n.value.id in qnames - {'queries'}]
        self.assertTrue(subs)
        for n in subs:
            self.assertIsInstance(n.slice, ast.Constant)
            self.assertEqual(n.slice.value, 'input')
        uses = [n for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id in qnames]
        self.assertEqual(len(uses), len(subs) + 2)  # the loop target plus the iterated 'queries'

    def test_factory_solve_signature_has_no_label_channel(self):
        src = program()[0]
        fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'solve')
        self.assertEqual([a.arg for a in fn.args.args], ['demonstrations', 'grid'])


class ContextAndFresh(unittest.TestCase):
    def test_no_demos_ambiguous_and_corrupt_rejected(self):
        can = canonical()
        q = can['test'][0]['input']
        _, solve = program()
        self.assertEqual(raised(solve, [], q), 'Ambiguous')
        self.assertEqual(raised(G.require_ba1aa698_evidence, [], [{'input': q}]), 'MissingBa1aa698Evidence')
        bad = [dict(can['train'][0], output=can['train'][2]['output'])]
        self.assertEqual(raised(solve, bad, q), 'Inconsistent')
        self.assertEqual(raised(G.require_ba1aa698_evidence, bad, [{'input': q}]), 'MissingBa1aa698Evidence')

    def test_seeded_native_episodes(self):
        checks = single = 0
        for k in range(12):
            random.seed(1_000_003 * (k + 1))
            pairs = [NATIVE.generate() for _ in range(4)]
            pal = list(range(10))
            random.Random(k).shuffle(pal)
            for d4 in range(8):
                ps = tx(pairs, d4, pal)
                demos, query = ps[:3], ps[3]
                src, solve = program(d4, pal)
                pred = solve(demos, query['input'])
                gate = G.require_ba1aa698_evidence(demos, [QueryTrap(query['input'])])[0]
                verify(src, {'train': demos, 'test': [{'input': query['input']}], 'solutions': [query['output']]})
                self.assertEqual(pred, gate)
                self.assertEqual(pred, query['output'])
                for d in demos:
                    self.assertEqual(solve([d], query['input']), query['output'])
                    single += 1
                checks += 1
        self.assertEqual((checks, single), (96, 288))


if __name__ == '__main__':
    unittest.main()

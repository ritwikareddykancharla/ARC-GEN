"""Portable focused tests for bd14c3bf (second independent review, v6).

Run:  PYTHONPATH=/Users/ritwika/projects/ARC-GEN \
      /Users/ritwika/projects/arc-agi2/.venv/bin/python -m unittest -v test_bd14c3bf_review_v6
(from this directory).  Query labels are only used by assertions after solving.
"""
import ast, importlib.util, json, random, sys, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
FORK = HERE.parent
sys.path.insert(0, str(FORK)); sys.path.insert(0, str(HERE))
from arc_agi2.runtime import reference
from arc_agi2.fixture_policy import fixture_basis
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.augmentation import transformed
from arc_agi2 import bd14c3bf_shape_family_evidence as E


def _load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


factory = _load(HERE / 'direct_factories/task_bd14c3bf.py', 'factory_bd14c3bf_v6').build_program
native = _load(FORK / 'tasks' / 'task_bd14c3bf.py', 'native_bd14c3bf_v6')
PAL = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]


def _solver(d4, pal):
    ns = {}; exec(factory(d4, pal), ns); return ns['solve']


def widths(s, a):
    # Mirrors native get_wide(); template (index 0) always uses the minimum.
    if s == 'A': return range(3 if a % 2 == 0 else 4, 6)
    if s == 'C': return range(3 if a % 2 == 0 else 2, 6)
    if s in 'HO': return range(3, 6)
    if s == 'L': return range(2, 6)
    if s == 'P': return [5] if a % 2 == 0 else range(2, 6)
    if s == 'Y': return [3, 5] if a % 2 == 0 else range(3, 6)
    if s == '8': return [5] if a % 2 == 0 else range(3, 6)


TEMPLATES = [(s, a, min(widths(s, a)), min(widths(s, 3 - a))) for s in 'ACHLOPY8' for a in range(4)]
VARIANTS = [(s, a, w, h) for s in 'ACHLOPY8' for a in range(4) for w in widths(s, a) for h in widths(s, 3 - a)]


def pair(t, v):
    return native.generate(size=20, wides=[t[2], v[2]], talls=[t[3], v[3]], brows=[0, 10], bcols=[0, 10],
                           angles=[t[1], v[1]], shapes=t[0] + v[0])


class Bd14c3bfReviewV6(unittest.TestCase):
    def test_template_size_is_always_minimum(self):
        # Exhaustive coverage relies on this:(a, b if i else a): index 0 is the template, so its range collapses to a.
        src = (FORK / 'tasks' / 'task_bd14c3bf.py').read_text()
        self.assertIn('return common.randint(a, b if i else a)', src)

    def test_exhaustive_native_domain_all_d4_one_palette(self):
        solvers = [_solver(d4, PAL) for d4 in range(8)]
        n = 0
        for t in TEMPLATES:
            for v in VARIANTS:
                p = pair(t, v)
                fam = E._predict(p['input'], 0, 2, ('family', 'd4'))
                self.assertEqual(fam, p['output'], ('independent gate family form', t, v))
                for d4 in range(8):
                    got = solvers[d4]([], transformed(p['input'], d4, PAL))
                    self.assertEqual(got, transformed(p['output'], d4, PAL), (t, v, d4)); n += 1
        self.assertEqual(n, 32 * 260 * 8)

    def test_canonical_fixture_16_variants(self):
        task = reference('bd14c3bf')[fixture_basis('bd14c3bf')['fixture']]
        for pal in (list(range(10)), PAL):
            for d4 in range(8):
                src = factory(d4, pal); audit_target('bd14c3bf', src)
                ep = {'train': [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in task['train']],
                      'test': [{'input': transformed(p['input'], d4, pal)} for p in task['test']],
                      'solutions': [transformed(p['output'], d4, pal) for p in task['test']]}
                verify(src, ep)
                E.require_bd14c3bf_evidence(ep['train'], ep['test'], pal)

    def test_gate_takes_query_inputs_only(self):
        task = reference('bd14c3bf')[fixture_basis('bd14c3bf')['fixture']]
        a = E.require_bd14c3bf_evidence(task['train'], [{'input': q['input']} for q in task['test']])
        bogus = [{'input': q['input'], 'output': [[9]]} for q in task['test']]
        b = E.require_bd14c3bf_evidence(task['train'], bogus)
        self.assertEqual(a, b)

    def test_solver_ignores_demonstrations_and_has_no_label_access(self):
        src = factory(3, PAL)
        tree = ast.parse(src)
        solve = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'solve'][0]
        names = {n.id for n in ast.walk(solve) if isinstance(n, ast.Name)}
        self.assertNotIn('demonstrations', names)
        self.assertNotIn('output', {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)})

    def test_old_counterexample_context_shortfall_then_resolved(self):
        ce = json.loads((HERE / 'reports/coverage-evidence/bd14c3bf/counterexample.json').read_text())
        ep, pal = ce['episode'], ce['palette']
        queries = [{'input': q['input']} for q in ep['test']]
        for d4 in range(8):  # rejection is D4-equivariant
            ident = list(range(10))
            dm = [{k: transformed(p[k], d4, ident) for k in ('input', 'output')} for p in ep['train']]
            qs = [{'input': transformed(q['input'], d4, ident)} for q in queries]
            with self.assertRaises(E.MissingBd14c3bfEvidence):
                E.require_bd14c3bf_evidence(dm, qs, pal)
            with self.assertRaises(E.MissingBd14c3bfEvidence):
                E.require_bd14c3bf_evidence(dm, qs)
            # The direct program is still exact (labels used only here, after solving).
            verify(factory(d4, pal), {'train': dm, 'test': qs, 'solutions': [transformed(ep['solutions'][0], d4, ident)]})
        # Same query, one demo replaced by a native Y-template scene that shows a 5-wide Y matching.
        y = native.generate(size=15, wides=[3, 5, 3], talls=[3, 3, 3], brows=[0, 0, 6], bcols=[0, 6, 0],
                            angles=[0, 0, 0], shapes='YYH')
        y = {k: transformed(y[k], ce['d4'], pal) for k in ('input', 'output')}
        demos = ep['train'][:-1] + [y]
        rep = E.require_bd14c3bf_evidence(demos, queries, pal)
        self.assertNotIn(['collapse', 'd4'], rep['surviving_hypotheses'])
        pred = E._predict(queries[0]['input'], pal[0], pal[2], tuple(rep['surviving_hypotheses'][0]))
        self.assertEqual(pred, ep['solutions'][0])
        self.assertEqual(_solver(ce['d4'], pal)([], queries[0]['input']), ep['solutions'][0])

    def test_gate_rejects_demos_fitting_nothing(self):
        task = reference('bd14c3bf')[fixture_basis('bd14c3bf')['fixture']]
        demo = json.loads(json.dumps(task['train'][0]))
        cells = [(r, c) for r, row in enumerate(demo['output']) for c, v in enumerate(row) if v == 1]
        r, c = cells[0]; demo['output'][r][c] = 2  # paint one stray cell
        with self.assertRaises(E.MissingBd14c3bfEvidence):
            E.require_bd14c3bf_evidence([demo], [{'input': task['test'][0]['input']}])

    def test_fresh_native_episodes_small(self):
        rng_seeds = [11, 12, 13]
        for s in rng_seeds:
            random.seed(s)
            pairs = [native.generate() for _ in range(4)]
            pal = list(range(10)); random.Random(s).shuffle(pal)
            for d4 in range(8):
                ep = {'train': [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in pairs[:3]],
                      'test': [{'input': transformed(pairs[3]['input'], d4, pal)}],
                      'solutions': [transformed(pairs[3]['output'], d4, pal)]}
                verify(factory(d4, pal), ep)


if __name__ == '__main__':
    unittest.main()

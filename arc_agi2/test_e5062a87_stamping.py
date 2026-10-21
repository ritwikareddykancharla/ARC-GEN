"""Focused tests for e5062a87. Run:
/Users/ritwika/projects/arc-agi2/.venv/bin/python -I e5062a87_tests.py -v
"""
import hashlib, importlib.util, json, random, sys, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORK = HERE.parent
sys.path.insert(0, str(FORK))
sys.path.insert(0, str(HERE))
from arc_agi2.runtime import reference, call
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.augmentation import transformed
from . import e5062a87_gate as G

TID = 'e5062a87'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


from .direct_factories.task_e5062a87 import build_program as FACTORY
NATIVE = load(FORK / 'tasks' / f'task_{TID}.py', 'gen_e5062a87')
CANON = reference(TID)['canonical']


def run(src, demos, query):
    ns = {'__name__': 'standalone_target'}
    exec(compile(src, '<t>', 'exec'), ns)
    try:
        return ns['solve'](json.loads(json.dumps(demos)), json.loads(json.dumps(query)))
    except Exception as e:
        return 'ABSTAIN:' + str(e)


def legal(colors, srows, scols, brows, bcols, size=10):
    """Independent re-statement of the constructor's draw() legality."""
    g = [[colors[r * size + c] for c in range(size)] for r in range(size)]
    for br, bc in zip(brows, bcols):
        for sr, sc in zip(srows, scols):
            g[br + sr][bc + sc] = 0
    fits = [(r, c) for r in range(size) for c in range(size)
            if all(r + sr < size and c + sc < size and g[r + sr][c + sc] == 0 for sr, sc in zip(srows, scols))]
    cells = [(br + sr, bc + sc) for br, bc in zip(brows, bcols) for sr, sc in zip(srows, scols)]
    return set(fits) <= set(zip(brows, bcols)) and len(cells) == len(set(cells)), fits


def fresh(index):
    seed = int(hashlib.sha256(f'factory-fresh:{TID}:{index}'.encode()).hexdigest()[:12], 16)
    random.seed(seed)
    return [call(NATIVE.generate, seconds=5) for _ in range(4)]


def ep_of(demos, query, d4, pal):
    return ([{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in demos],
            transformed(query['input'], d4, pal), transformed(query['output'], d4, pal))


class FixtureTests(unittest.TestCase):
    def test_canonical_all_variants_exact(self):
        pals = [list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5], [9, 0, 4, 1, 8, 6, 2, 3, 5, 7], [5, 4, 7, 2, 0, 1, 6, 9, 3, 8]]
        for pal in pals:
            for d4 in range(8):
                src = FACTORY(d4, pal)
                audit_target(TID, src)
                ep = {'train': [{k: transformed(p[k], d4, pal) for k in ('input', 'output')} for p in CANON['train']],
                      'test': [{'input': transformed(p['input'], d4, pal)} for p in CANON['test']],
                      'solutions': [transformed(p['output'], d4, pal) for p in CANON['test']]}
                verify(src, ep)

    def test_d4_never_selects(self):
        pal = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
        self.assertEqual(len({FACTORY(d, pal) for d in range(8)}), 1)

    def test_all_fits_refuted_by_canonical_pair0(self):
        # Canonical train pair 0 (1x4 bar): fit at row 1, x=3..6 is all-0 but unpainted.
        i, o = CANON['train'][0]['input'], CANON['train'][0]['output']
        self.assertEqual(i[1][3:7], [0, 0, 0, 0])
        self.assertEqual(o[1][3:7], [0, 0, 0, 0])
        opts = G.stamp_options(i, 0, 2)
        self.assertNotEqual(G.paint(i, opts, ('none', False, False, 'union'), 2), o)

    def test_fixture_survivors_agree_on_test(self):
        st, ans, alive = G.gate([(p['input'], p['output']) for p in CANON['train']], CANON['test'][0]['input'], 0, 2)
        self.assertEqual(st, 'identified')
        self.assertEqual(ans, CANON['test'][0]['output'])
        self.assertTrue(alive)
        self.assertNotIn(('none', False, False, 'union'), alive)


class ConstructorWitnessTests(unittest.TestCase):
    """Canonical pairs 0 and 1 are latent-labelled illegal draws."""

    def test_pair0_identical_input_different_output(self):
        p0 = CANON['train'][0]
        colors = [v for row in p0['input'] for v in row]
        colors = [0 if v == 2 else v for v in colors]  # template cells are blackened anyway
        # canonical parameters: illegal (unplanned fit (1,3))
        ok, fits = legal(colors, [0] * 4, [0, 1, 2, 3], [5, 5], [1, 6])
        self.assertFalse(ok)
        self.assertIn((1, 3), fits)
        # random-branch-reachable parameters: legal, same input, different label
        ok2, _ = legal(colors, [0] * 4, [0, 1, 2, 3], [5, 5, 1], [1, 6, 3])
        self.assertTrue(ok2)
        alt = NATIVE.generate(colors=colors, srows=[0] * 4, scols=[0, 1, 2, 3], brows=[5, 5, 1], bcols=[1, 6, 3])
        self.assertEqual(alt['input'], p0['input'])
        self.assertNotEqual(alt['output'], p0['output'])
        self.assertEqual(alt['output'][1][3:7], [2, 2, 2, 2])

    def test_pair1_diamond_illegal(self):
        p1 = CANON['train'][1]
        colors = [0 if v == 2 else v for row in p1['input'] for v in row]
        ok, fits = legal(colors, [0, 1, 1, 2], [1, 0, 2, 1], [0, 1, 5, 6, 7], [5, 7, 6, 0, 5])
        self.assertFalse(ok)
        self.assertIn((2, 6), fits)
        self.assertIn((5, 1), fits)

    def test_test_pair_and_pair2_legal(self):
        for p, sr, sc, br, bc in [(CANON['train'][2], [0, 1, 2, 2], [0, 0, 0, 1], [7, 2, 2, 5], [7, 1, 3, 3]),
                                  (CANON['test'][0], [0, 0, 1, 1, 2, 2], [0, 1, 0, 1, 0, 1], [4, 2, 7], [5, 0, 8])]:
            colors = [0 if v == 2 else v for row in p['input'] for v in row]
            self.assertTrue(legal(colors, sr, sc, br, bc)[0])


class AmbiguityTests(unittest.TestCase):
    def test_context_shortfall_episode0_abstains_then_resolves(self):
        pairs = fresh(0)
        demos, query = pairs[:3], pairs[3]
        st, answers, alive = G.gate([(p['input'], p['output']) for p in demos], query['input'], 0, 2)
        self.assertEqual(st, 'ambiguous')
        self.assertGreaterEqual(len(answers), 2)  # concrete rival outputs on the same query
        for d4 in range(8):
            pal = list(range(10)); random.Random(d4).shuffle(pal)
            d, q, _ = ep_of(demos, query, d4, pal)
            self.assertTrue(str(run(FACTORY(d4, pal), d, q)).startswith('ABSTAIN'))
        # keep the query, resample demos until evidence appears
        for _ in range(50):
            demos = [call(NATIVE.generate, seconds=5) for _ in range(3)]
            st, ans, _ = G.gate([(p['input'], p['output']) for p in demos], query['input'], 0, 2)
            if st == 'identified':
                break
        self.assertEqual(st, 'identified')
        for d4 in range(8):
            pal = list(range(10)); random.Random(100 + d4).shuffle(pal)
            d, q, a = ep_of(demos, query, d4, pal)
            self.assertEqual(run(FACTORY(d4, pal), d, q), a)

    def test_program_and_independent_gate_agree(self):
        n_amb = n_id = 0
        for index in range(1000, 1150):
            pairs = fresh(index)
            demos, query = pairs[:3], pairs[3]
            st, ans, _ = G.gate([(p['input'], p['output']) for p in demos], query['input'], 0, 2)
            d4 = index % 8
            pal = list(range(10)); random.Random(index).shuffle(pal)
            d, q, a = ep_of(demos, query, d4, pal)
            got = run(FACTORY(d4, pal), d, q)
            if st == 'identified':
                n_id += 1
                self.assertEqual(ans, query['output'])  # gate answer == generator label (checked after)
                self.assertEqual(got, a)
            else:
                n_amb += 1
                self.assertTrue(str(got).startswith('ABSTAIN'))
        self.assertGreater(n_amb, 0)
        self.assertGreater(n_id, 0)

    def test_hard_case_preserved_thin_copy_beside_open_window(self):
        # Find fresh native queries where the thick filter fires on a REAL copy;
        # with demos that refute that filter, the program must still paint it.
        found = 0
        for index in range(2000, 2600):
            pairs = fresh(index)
            q = pairs[3]
            opts = G.stamp_options(q['input'], 0, 2)
            if not any(s['thick'] for s in opts):
                continue
            demos = pairs[:3]
            for _ in range(60):
                st, _, _ = G.gate([(p['input'], p['output']) for p in demos], q['input'], 0, 2)
                if st == 'identified':
                    break
                demos = [call(NATIVE.generate, seconds=5) for _ in range(3)]
            self.assertEqual(st, 'identified')
            pal = list(range(10)); random.Random(index).shuffle(pal)
            d, qi, a = ep_of(demos, q, index % 8, pal)
            self.assertEqual(run(FACTORY(index % 8, pal), d, qi), a)
            found += 1
            if found >= 5:
                break
        self.assertGreaterEqual(found, 5)

    def test_synthetic_ambiguity_witness(self):
        # Demos with solid 2x3 templates cannot refute the thick filter; a thin
        # bar query beside an open 2x2 window then has two consistent answers.
        demo_in = [[5] * 10 for _ in range(10)]
        for r in range(2):
            for c in range(3):
                demo_in[r][c] = 2
                demo_in[6 + r][4 + c] = 0
        demo_out = [row[:] for row in demo_in]
        for r in range(2):
            for c in range(3):
                demo_out[6 + r][4 + c] = 2
        q = [[5] * 10 for _ in range(10)]
        q[0][0:4] = [2, 2, 2, 2]
        q[5][2:6] = [0, 0, 0, 0]
        q[4][4] = q[4][5] = 0
        demos = [{'input': demo_in, 'output': demo_out}]
        st, answers, _ = G.gate([(demo_in, demo_out)], q, 0, 2)
        self.assertEqual(st, 'ambiguous')
        self.assertEqual(run(FACTORY(0, list(range(10))), demos, q)[:8], 'ABSTAIN:')


if __name__ == '__main__':
    unittest.main()

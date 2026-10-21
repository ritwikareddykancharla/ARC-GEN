import unittest, json, importlib
from pathlib import Path
from .colour_evidence import MissingColourEvidence

def reference(tid):
    return json.loads((Path(__file__).parent / 'references' / (tid + '.json')).read_text())

class CursorHypothesisTests(unittest.TestCase):

    def setUp(self):
        self.pal = list(range(10))
        self.f = {}
        self.e = {}
        self.ns = {}
        for tid in ('dd2401ed',):
            self.f[tid] = importlib.import_module('arc_agi2.direct_factories.task_' + tid)
            self.e[tid] = importlib.import_module('arc_agi2.' + {'b1986d4b': 'square_stack_hypothesis_evidence', 'dd2401ed': 'cursor_recolour_evidence'}[tid])
            ns = {}
            exec(self.f[tid].build_program(0, self.pal), ns)
            self.ns[tid] = ns

    def test_both_canonical_and_poisoned_query(self):
        for tid in self.f:
            task = reference(tid)['canonical']
            query = task['test'][0]
            self.e[tid].require_evidence(task['train'], [{'input': query['input'], 'output': [['POISON']]}], self.pal)
            self.assertEqual(self.ns[tid]['solve'](task['train'], query['input']), query['output'])

    def test_even_cursor_query_requires_disambiguation(self):
        from tasks.task_dd2401ed import generate

        def pair(even):
            colors = [0] * 105
            for r, c in [(0, 0), (1, 3), (2, 9)] + ([(3, 1)] if even else []):
                colors[15 * r + c] = 1
            return generate(cursor=2, extra=0, colors=colors)
        demo = pair(False)
        query = pair(True)
        tid = 'dd2401ed'
        with self.assertRaises(MissingColourEvidence):
            self.e[tid].require_evidence([demo], [{'input': query['input']}], self.pal)
        with self.assertRaises(ValueError):
            self.ns[tid]['solve']([demo], query['input'])
        self.e[tid].require_evidence([query], [{'input': query['input']}], self.pal)
        self.assertEqual(self.ns[tid]['solve']([query], query['input']), query['output'])

    def test_orientation_not_factory_oracle(self):
        for tid, f in self.f.items():
            self.assertEqual(f.build_program(0, self.pal), f.build_program(7, self.pal))

    def test_no_demo_or_bad_label_rejected(self):
        for tid in self.f:
            task = reference(tid)['canonical']
            g = task['test'][0]['input']
            with self.assertRaises(MissingColourEvidence):
                self.e[tid].require_evidence([], [{'input': g}], self.pal)
            with self.assertRaises(MissingColourEvidence):
                self.e[tid].require_evidence([{'input': task['train'][0]['input'], 'output': [[9]]}], [{'input': g}], self.pal)
if __name__ == '__main__':
    unittest.main()

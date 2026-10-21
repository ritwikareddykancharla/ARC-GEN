"""Observable stacking evidence must not depend on hidden query answers."""
import unittest
from arc_agi2.runtime import reference
from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import require_colour_evidence, MissingColourEvidence
from arc_agi2.slide_stack_c6e1b8da_evidence import IntrinsicAmbiguity
from arc_agi2.direct_factories.task_c6e1b8da import build_program
from tasks.task_c6e1b8da import generate


class SlideStackTests(unittest.TestCase):
    def test_original_fixture_all_views(self):
        task = reference('c6e1b8da')['canonical']
        for palette in (list(range(10)), [3,9,0,7,2,8,1,6,4,5]):
            for view in range(8):
                demos = [{k: transformed(p[k], view, palette)
                          for k in ('input', 'output')} for p in task['train']]
                ns = {}; exec(build_program(view, palette), ns)
                for pair in task['test']:
                    query = transformed(pair['input'], view, palette)
                    require_colour_evidence('c6e1b8da', demos,
                                            [{'input': query}], palette, view)
                    self.assertEqual(ns['solve'](demos, query),
                                     transformed(pair['output'], view, palette))

    def test_hidden_query_label_is_never_accessed(self):
        class Query(dict):
            def __getitem__(self, key):
                if key == 'output': raise AssertionError('query label read')
                return super().__getitem__(key)
            def __contains__(self, key):
                if key == 'output': raise AssertionError('query label tested')
                return super().__contains__(key)
        task = reference('c6e1b8da')['canonical']
        require_colour_evidence('c6e1b8da', task['train'],
                                [Query(input=task['test'][0]['input'], output=[[99]])])

    def test_hidden_order_ambiguity_is_rejected(self):
        args = dict(wides=[3,9,3,3], talls=[9,3,3,3], brows=[2,5,5,14],
                    bcols=[8,6,8,1], colors=[1,2,3,4], angles=[-1,-1,1,1],
                    lengths=[1,1,3,1], downs=[1,1,1,1])
        other = {k: [v[1], v[0]] + v[2:] for k,v in args.items()}
        a, b = generate(**args), generate(**other)
        self.assertEqual(a['input'], b['input'])
        self.assertNotEqual(a['output'], b['output'])
        with self.assertRaises(IntrinsicAmbiguity):
            require_colour_evidence('c6e1b8da', [], [{'input': a['input']}])
        with self.assertRaises(MissingColourEvidence):
            require_colour_evidence('c6e1b8da', [a], [])


if __name__ == '__main__': unittest.main()

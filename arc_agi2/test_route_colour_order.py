"""Route choices must not depend on an unobserved colour priority."""
import hashlib
import itertools
import json
import unittest

from tasks import task_f8f52ecc as generator


class RouteColourOrderTests(unittest.TestCase):
    chains = [
        (2, [(0, 4), (3, 4)], [(0, 4), (1, 4), (3, 4)]),
        (3, [(2, 1), (2, 2), (5, 2), (5, 5)], [(2, 1), (2, 2), (5, 5)]),
    ]

    def test_hidden_earlier_route_cannot_supply_missing_wall(self):
        inp, out = generator._render(8, 8, self.chains, [], [])
        ascending = inp
        for col in (2, 3):
            finals = generator._settle(ascending, col, 5000)
            self.assertEqual(len(finals), 1)
            ascending = [list(row) for row in finals.pop()]
        self.assertEqual(ascending, out)
        reversed_first = generator._settle(inp, 3, 5000)
        expected = [row[:] for row in inp]
        for r, c in generator._route(self.chains[1][1]): expected[r][c] = 3
        self.assertNotEqual(reversed_first, {tuple(map(tuple, expected))})
        with self.assertRaisesRegex(ValueError, 'not forced'):
            generator.generate(height=8, width=8, chains=self.chains)

    def test_visible_wall_preserves_multicolour_route_problem(self):
        pair = generator.generate(height=8, width=8, chains=self.chains,
                                  walls=[(2, 3, 2, 3)])
        for order in itertools.permutations((2, 3)):
            state = pair['input']
            for col in order:
                finals = generator._settle(state, col, 5000)
                self.assertEqual(len(finals), 1)
                state = [list(row) for row in finals.pop()]
            self.assertEqual(state, pair['output'])

    def test_original_fixtures_unchanged(self):
        digest = hashlib.sha256(json.dumps(generator.validate(), sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, '9169bde83c66663a62de1811db85e600ebc6d60290567411fba147eea9438dfa')


if __name__ == '__main__':
    unittest.main()

"""Complete shared patterns without inventing alignment tie-breaks."""
import hashlib
import json
import unittest

from tasks import task_f8cc533f as generator
from .augmentation import transformed


class SharedPatternCompletionTests(unittest.TestCase):
    def test_raw_evidence_union_disambiguates_rotated_fragment(self):
        # The old heuristic symmetrised each fragment independently, inventing
        # evidence for two equally scored placements of the narrow fragment.
        g = [[3]*16 for _ in range(16)]
        for r in range(2, 5):
            for c in range(12, 15): g[r][c] = 8
        g[2][13] = 3
        for r, c in [(9,6), (10,5), (10,6), (11,5), (11,6)]: g[r][c] = 0
        expected = [row[:] for row in g]
        for r in range(9, 12):
            for c in range(5, 8): expected[r][c] = 0
        expected[2][13] = 8
        for pal in [list(range(10)), [3,9,0,7,2,8,1,6,4,5]]:
            for d4 in range(8):
                self.assertEqual(generator._unique_shared_completion(transformed(g,d4,pal)),
                                 transformed(expected,d4,pal))

    def test_identical_input_with_two_valid_placements_is_rejected(self):
        g = [[0]*15 for _ in range(15)]
        for r in range(2,5):
            for c in range(2,4): g[r][c] = 1
        for r in range(9,12):
            for c in range(10,12): g[r][c] = 2
        kwargs = dict(width=15,height=15,length=5,brows=[1,8],
                      bcolors=[1,2],colors=sum(g,[]))
        a = generator.generate(bcols=[1,8], **kwargs)
        b = generator.generate(bcols=[0,9], **kwargs)
        self.assertEqual(a['input'], b['input'])
        self.assertNotEqual(a['output'], b['output'])
        for d4 in range(8):
            with self.assertRaisesRegex(ValueError, 'ambiguous shared pattern'):
                generator._unique_shared_completion(transformed(g,d4,list(range(10))))

    def test_exhausted_search_is_not_a_uniqueness_certificate(self):
        p = generator.validate()['train'][0]
        with self.assertRaisesRegex(ValueError, 'budget exceeded'):
            generator._unique_shared_completion(p['input'], budget=1)

    def test_original_fixtures_unchanged(self):
        fixtures = generator.validate()
        digest = hashlib.sha256(json.dumps(fixtures, sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, '76b40c1a4114dc742fb5b6e52e38571712cdcb751907864c6a7248ce250c32c7')
        for pair in fixtures['train'] + fixtures['test']:
            self.assertEqual(generator._unique_shared_completion(pair['input']), pair['output'])


if __name__ == '__main__':
    unittest.main()

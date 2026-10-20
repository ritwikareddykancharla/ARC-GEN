import unittest

from tasks.task_e88171ec import _unique_largest_zero_rectangle, validate


class ZeroRectangleSamplingTests(unittest.TestCase):
    @staticmethod
    def scene(*boxes):
        g = [[2]*16 for _ in range(16)]
        for top, bottom, left, right in boxes:
            for r in range(top, bottom+1):
                for c in range(left, right+1):
                    g[r][c] = 0
        return g

    def test_unique_planted_rectangle(self):
        box = (2, 5, 2, 5)
        self.assertTrue(_unique_largest_zero_rectangle(self.scene(box), box))

    def test_equal_area_competitor_is_rejected(self):
        box = (2, 5, 2, 5)
        self.assertFalse(_unique_largest_zero_rectangle(
            self.scene(box, (9, 12, 9, 12)), box))

    def test_three_wide_larger_competitor_is_rejected(self):
        # A solver restricted to side>=4 would miss this 3x6 competitor.
        box = (2, 5, 2, 5)
        self.assertFalse(_unique_largest_zero_rectangle(
            self.scene(box, (9, 11, 8, 13)), box))

    def test_extension_of_planted_rectangle_is_rejected(self):
        box = (2, 5, 2, 5)
        self.assertFalse(_unique_largest_zero_rectangle(
            self.scene((2, 5, 2, 6)), box))

    def test_original_fixtures_already_have_unique_maximum(self):
        fixtures = validate()
        for pair in fixtures['train']+fixtures['test']:
            changed = [(r, c) for r, row in enumerate(pair['input'])
                       for c, ink in enumerate(row) if pair['output'][r][c] != ink]
            box = (min(r for r, c in changed)-1, max(r for r, c in changed)+1,
                   min(c for r, c in changed)-1, max(c for r, c in changed)+1)
            self.assertTrue(_unique_largest_zero_rectangle(pair['input'], box))


if __name__ == '__main__':
    unittest.main()

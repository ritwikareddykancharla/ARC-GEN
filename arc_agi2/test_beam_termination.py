import unittest

from tasks.task_e87109e9 import _trace


class BeamTerminationTests(unittest.TestCase):
    def test_long_finite_path_is_not_silently_truncated(self):
        body = [[1] for _ in range(2105)]
        body[0][0] = 8
        output, stats = _trace(body, 1, (0, 0, 1), [])
        self.assertEqual(output, [[8] for _ in body])
        self.assertFalse(stats['loop'])

    def test_boxed_beam_terminates_on_repeated_state(self):
        body = [[2, 2, 2], [2, 8, 2], [2, 2, 2]]
        output, stats = _trace(body, 1, (1, 1, 1), [(2, 'L')])
        self.assertEqual(output, body)
        self.assertTrue(stats['loop'])
        self.assertEqual(stats['turns'], 16)  # Four turns for each initial ray.


if __name__ == '__main__':
    unittest.main()

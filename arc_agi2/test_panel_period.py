"""A unique divider-free panel prevents every smaller false divider period.

The native c3202e5a sampler uses panel size 3..5, at least three panels
per axis, divider D != 0, foreground F != D and F != 0. Other panels
contain 0 and at least two nonzero colours. No random-domain restriction
is added here. Explicit fixtures are separately checked by the host audit.
"""
import unittest
import numpy as np
from arc_agi2.augmentation import transformed
from arc_agi2.direct_factories.task_c3202e5a import build_program
from tasks import task_c3202e5a as task


def hostile_pair(s, k, target, false_period=None):
    """Make distractors almost solid divider ink, preserving native invariants.

When a false period is specified, keep every false line outside the target
solid D; the target itself must be what invalidates the proposed period.
"""
    n = (s + 1) * k - 1
    g = [[3] * n for _ in range(n)]
    tr, tc = target
    for br in range(k):
        for bc in range(k):
            r0, c0 = br * (s + 1), bc * (s + 1)
            if (br, bc) == target:
                for r in range(s):
                    for c in range(s):
                        g[r0 + r][c0 + c] = 7
                g[r0][c0] = 0
            else:
                free = [(r, c) for r in range(s) for c in range(s)
                        if false_period is None or
                        ((r0+r+1) % false_period and (c0+c+1) % false_period)]
                assert len(free) >= 2
                for colour, (r, c) in zip((0, 7), free):
                    g[r0+r][c0+c] = colour
    pair = task.generate(minisize=s, megasize=k, colors=sum(g, []))
    assert pair['output'] == [[0 if r == c == 0 else 7 for c in range(s)] for r in range(s)]
    return pair


class PanelPeriodTests(unittest.TestCase):
    palettes = [list(range(10)), [3,9,0,7,2,8,1,6,4,5]]

    @classmethod
    def setUpClass(cls):
        cls.programs = {}
        for i, pal in enumerate(cls.palettes):
            for d4 in range(8):
                ns = {}
                exec(build_program(d4, pal), ns)
                cls.programs[i, d4] = ns

    def test_every_native_geometry_and_target_position_with_divider_dense_distractors(self):
        cases = 0
        for s in range(3,6):
            for k in range(3,7):
                n = (s+1)*k-1
                if n > 30:
                    continue
                for br in range(k):
                    for bc in range(k):
                        p = hostile_pair(s, k, (br, bc))
                        for i,pal in enumerate(self.palettes):
                            for d4 in range(8):
                                g = transformed(p['input'],d4,pal)
                                ns = self.programs[i,d4]
                                for axis in (0,1):
                                    self.assertEqual(ns['_period_lines'](np.array(g),axis),
                                                     (list(range(s,n,s+1)),pal[3]))
                                self.assertEqual(ns['solve']([],g), transformed(p['output'],d4,pal))
                        cases += 1
        self.assertEqual(cases,222)

    def test_target_blocks_every_smaller_candidate_period(self):
        cases = 0
        for s in range(3,6):
            for k in range(3,7):
                n = (s+1)*k-1
                if n > 30:
                    continue
                for q in range(2,s+1):
                    if (n+1) % q:
                        continue
                    for br in range(k):
                        for bc in range(k):
                            p = hostile_pair(s,k,(br,bc),q)
                            g = p['input']; cuts = list(range(q-1,n,q))
                            # Without the foreground panel, every candidate cut
                            # really is a solid divider-colour line.
                            restored = [row[:] for row in g]
                            for r in range(br*(s+1),br*(s+1)+s):
                                for c in range(bc*(s+1),bc*(s+1)+s):
                                    restored[r][c] = 3
                            self.assertTrue(all(all(v==3 for v in restored[r]) for r in cuts))
                            self.assertTrue(all(all(row[c]==3 for row in restored) for c in cuts))
                            for i,pal in enumerate(self.palettes):
                                for d4 in range(8):
                                    x = transformed(g,d4,pal); ns = self.programs[i,d4]
                                    self.assertEqual(ns['solve']([],x),transformed(p['output'],d4,pal))
                            cases += 1
        self.assertGreater(cases,222)

    def test_ambiguous_panel_and_missing_structure_fail_closed(self):
        ns = self.programs[0,0]
        p = hostile_pair(3,3,(0,0))
        # Two qualifying panels must not be resolved by colour count or order.
        for r in range(3):
            for c in range(3):
                p['input'][r+4][c+4] = p['output'][r][c]
        with self.assertRaisesRegex(ValueError,'exactly one'):
            ns['solve']([],p['input'])
        with self.assertRaisesRegex(ValueError,'dividers'):
            ns['solve']([],[[0,7],[7,0]])


if __name__ == '__main__':
    unittest.main()

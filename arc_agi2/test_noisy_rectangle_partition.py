import random
import unittest

# The test harness (not the factory or emitted program) execs the emitted source.
from arc_agi2.direct_factories.task_de809cff import build_program


def _gen(w, h, rects, holes, foreign, strays):
    clean = [[0] * w for _ in range(h)]
    for c, t, l, b, r in rects:
        for y in range(t, b + 1):
            for x in range(l, r + 1):
                clean[y][x] = c
    g = [row[:] for row in clean]
    for y, x in holes:
        g[y][x] = 0
    for y, x, c in foreign:
        g[y][x] = c
    for y, x, c in strays:
        g[y][x] = c
    pal = sorted(set(v for row in g for v in row if v))
    out = [row[:] for row in clean]
    marks = sorted(set((y, x) for y, x in holes if clean[y][x]))
    for y, x in marks:
        own = clean[y][x]
        others = [c for c in pal if c != own]
        fr = others[0] if others else own
        for yy in range(max(0, y - 1), min(h, y + 2)):
            for xx in range(max(0, x - 1), min(w, x + 2)):
                out[yy][xx] = fr
    for y, x in marks:
        out[y][x] = 8
    return g, out


def _d4(g, k):
    g = [list(r) for r in g]
    if k >= 4:
        g = [row[::-1] for row in g]
    for _ in range(k % 4):
        g = [list(r) for r in zip(*g[::-1])]
    return g


def _pal(g, p):
    return [[p[v] for v in row] for row in g]


def _load(d4, palette):
    ns = {}
    exec(build_program(d4, palette), ns)
    return ns['solve']


ADV = (20, 20, [(4, 5, 2, 12, 15), (3, 0, 0, 7, 5), (3, 0, 7, 7, 12)],
       [(2, 2), (2, 10), (10, 9)], [(6, 6, 3)], [(17, 18, 3)])
P1 = (20, 20, [(3, 0, 1, 9, 12), (4, 7, 6, 17, 19), (3, 14, 0, 19, 9)],
      [(0, 3), (1, 7), (1, 8), (2, 6), (3, 7), (3, 12), (6, 3), (9, 16), (10, 10), (12, 13),
       (13, 12), (14, 2), (15, 17), (16, 12), (16, 13), (17, 0), (17, 4)], [],
      [(2, 15, 3), (4, 14, 4), (4, 18, 3), (11, 1, 3), (11, 3, 4), (13, 4, 4), (19, 14, 4)])
P2 = (20, 20, [(1, 0, 0, 10, 10), (2, 8, 6, 19, 19)],
      [(2, 5), (3, 4), (7, 5), (9, 4), (10, 14), (14, 8), (14, 14), (14, 17), (16, 16),
       (18, 11), (18, 14), (19, 7)], [(7, 7, 2), (7, 9, 2)],
      [(1, 14, 2), (2, 11, 1), (2, 18, 2), (4, 12, 1), (4, 15, 2), (5, 18, 1), (7, 15, 2),
       (11, 1, 1), (12, 4, 1), (15, 1, 1), (16, 5, 2), (18, 2, 1)])
T = (30, 30, [(6, 1, 8, 10, 29), (1, 5, 1, 19, 20), (6, 19, 4, 29, 25)],
     [(2, 10), (2, 18), (4, 25), (5, 26), (6, 4), (6, 13), (7, 28), (10, 6), (10, 16), (11, 16),
      (13, 1), (13, 9), (15, 20), (17, 3), (18, 16), (21, 14), (22, 22), (23, 6), (24, 17),
      (24, 22), (26, 4), (26, 11), (28, 21), (28, 22)],
     [(4, 10, 1), (7, 21, 1), (9, 20, 6), (19, 8, 1)],
     [(0, 4, 6), (3, 6, 6), (4, 2, 1), (11, 27, 6), (12, 22, 1), (15, 26, 1), (17, 29, 6),
      (18, 22, 6), (22, 1, 6), (22, 27, 6), (23, 3, 6), (23, 29, 6), (26, 0, 1), (26, 26, 6),
      (28, 28, 6)])


class Tests(unittest.TestCase):
    def test_gap1_foreign_bridge_not_merged(self):
        g, out = _gen(*ADV)
        solve = _load(0, list(range(10)))
        res = solve([], g)
        self.assertEqual(res, out)
        for y in range(5):
            self.assertEqual(res[y][6], 0)
        for y in (5, 6, 7):
            self.assertEqual(res[y][6], 4)

    def test_scenes_all_d4_and_palettes(self):
        rnd = random.Random(12345)
        scenes = [_gen(*s) for s in (P1, P2, T, ADV)]
        for k in range(8):
            for _ in range(3):
                p = list(range(10))
                rnd.shuffle(p)
                solve = _load(k, p)
                demos = [{'input': _pal(_d4(i, k), p), 'output': _pal(_d4(o, k), p)} for i, o in scenes[:2]]
                for i, o in scenes:
                    self.assertEqual(solve(demos, _pal(_d4(i, k), p)), _pal(_d4(o, k), p))

    def test_adversary_is_constructor_valid(self):
        from tasks.task_de809cff import _recognisable, _dominance_ok
        w,h,rects,holes,foreign,strays=ADV
        g,out=_gen(*ADV)
        self.assertTrue(_recognisable(g,rects,w,h))
        self.assertTrue(_dominance_ok(g,rects))

    def test_no_source_answer_access(self):
        g,out=_gen(*T)
        self.assertEqual(_load(0,list(range(10)))([],g),out)
        self.assertEqual(_load(0,list(range(10)))([{'input':[[9]],'output':[[9]]}],g),out)

    def test_unknown_third_colour_rejected(self):
        g,_=_gen(*T);g[0][0]=3
        with self.assertRaises(ValueError):_load(0,list(range(10)))([],g)


if __name__ == '__main__':
    unittest.main()

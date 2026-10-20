def build_program(d4, palette):
    N = 10

    def fwd(y, x):
        if d4 >= 4:
            x = N - 1 - x
        for _ in range(d4 % 4):
            y, x = x, N - 1 - y
        return y, x

    def classify(points):
        if all(p[0] == 0 for p in points):
            return 'top'
        if all(p[0] == N - 1 for p in points):
            return 'bottom'
        if all(p[1] == 0 for p in points):
            return 'left'
        return 'right'

    edge_a = classify([fwd(0, x) for x in range(N)])
    edge_b = classify([fwd(y, N - 1) for y in range(N)])
    bg = int(palette[0])
    red = int(palette[2])

    src = '''import numpy as np

EDGE_A = %r
EDGE_B = %r
BG = %d
RED = %d


def _idx(edge, h, w):
    if edge == 'top' or edge == 'left':
        return 0
    if edge == 'bottom':
        return h - 1
    return w - 1


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    ia = _idx(EDGE_A, h, w)
    ib = _idx(EDGE_B, h, w)
    if EDGE_A in ('top', 'bottom'):
        ra, cb = ia, ib
        cols = [x for x in range(w) if x != cb and g[ra, x] != BG]
        rows = [y for y in range(h) if y != ra and g[y, cb] != BG]
    else:
        ca, rb = ia, ib
        rows = [y for y in range(h) if y != rb and g[y, ca] != BG]
        cols = [x for x in range(w) if x != ca and g[rb, x] != BG]
    for y in rows:
        for x in cols:
            if out[y, x] == BG:
                out[y, x] = RED
    return out.tolist()
''' % (edge_a, edge_b, bg, red)
    return src

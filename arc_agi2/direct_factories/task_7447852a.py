import numpy as np

_BODY = '''

def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    n_rows = len(g)
    n_cols = len(g[0]) if n_rows else 0
    if LONG_AXIS == 1:
        L, C = n_cols, n_rows
    else:
        L, C = n_rows, n_cols
    if L == 0 or C == 0:
        return g
    mid = C // 2

    def put(t, s):
        if t < 0 or t >= L or s < 0 or s >= C:
            return
        lt = t if LONG_SIGN > 0 else L - 1 - t
        cs = s if CROSS_SIGN > 0 else C - 1 - s
        if LONG_AXIS == 1:
            y, x = cs, lt
        else:
            y, x = lt, cs
        if g[y][x] == BG:
            g[y][x] = FILL

    c = 0
    k = 0
    while c - 1 < L:
        wide = C - 1 if k % 2 == 0 else 0
        for t in (c - 1, c, c + 1):
            put(t, wide)
        put(c, mid)
        c += 6
        k += 1
    return g
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    H, W = 3, 7
    g = np.arange(H * W).reshape(H, W)
    if d4 >= 4:
        g = g[:, ::-1]
    for _ in range(d4 % 4):
        g = np.rot90(g, -1)

    def pos(v):
        ys, xs = np.nonzero(g == v)
        return int(ys[0]), int(xs[0])

    p00 = pos(0)
    p01 = pos(1)
    p10 = pos(W)
    if p01[0] != p00[0]:
        long_axis = 0
        long_sign = p01[0] - p00[0]
        cross_sign = p10[1] - p00[1]
    else:
        long_axis = 1
        long_sign = p01[1] - p00[1]
        cross_sign = p10[0] - p00[0]
    header = ('LONG_AXIS = %d\nLONG_SIGN = %d\nCROSS_SIGN = %d\nBG = %d\nFILL = %d\n'
              % (long_axis, long_sign, cross_sign, int(palette[0]), int(palette[4])))
    return header + _BODY

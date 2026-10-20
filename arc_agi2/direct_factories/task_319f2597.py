def build_program(d4, palette):
    zero = int(palette[0])
    keep = int(palette[2])
    src = '''import numpy as np

ZERO = %d
KEEP = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    ys, xs = np.where(g == ZERO)
    rows = sorted(set(ys.tolist()))
    cols = sorted(set(xs.tolist()))
    for y in rows:
        r = g[y, :]
        r[r != KEEP] = ZERO
        g[y, :] = r
    for x in cols:
        c = g[:, x]
        c[c != KEEP] = ZERO
        g[:, x] = c
    return g.tolist()
''' % (zero, keep)
    return src

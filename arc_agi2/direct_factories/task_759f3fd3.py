def build_program(d4, palette):
    bg = int(palette[0])
    line = int(palette[3])
    ring = int(palette[4])
    src = '''import numpy as np

BG = %d
LINE = %d
RING = %d

def _find_cross(g):
    H, W = g.shape
    rows = [y for y in range(H) if np.all(g[y, :] == LINE)]
    cols = [x for x in range(W) if np.all(g[:, x] == LINE)]
    if not rows:
        rows = [y for y in range(H) if np.all(g[y, :] != BG)]
    if not cols:
        cols = [x for x in range(W) if np.all(g[:, x] != BG)]
    if not rows or not cols:
        return None
    return rows[0], cols[0]

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    found = _find_cross(g)
    if found is None:
        return g.tolist()
    cy, cx = found
    ys, xs = np.mgrid[0:H, 0:W]
    d = np.maximum(np.abs(ys - cy), np.abs(xs - cx))
    maxd = int(d.max())
    for r in range(2, maxd + 1, 2):
        mask = (d == r) & (g == BG)
        if mask.any():
            g[mask] = RING
    return g.tolist()
''' % (bg, line, ring)
    return src

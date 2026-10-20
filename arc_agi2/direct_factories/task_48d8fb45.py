def build_program(d4, palette):
    k = d4 % 4
    dr, dc = 1, 0
    for _ in range(k):
        dr, dc = dc, -dr
    marker = int(palette[5])
    src = '''import numpy as np

MARKER = %d
DR = %d
DC = %d

def _find_marker(g):
    ys, xs = np.where(g == MARKER)
    if len(ys) > 0:
        return int(ys[0]), int(xs[0])
    vals, counts = np.unique(g, return_counts=True)
    for v, c in zip(vals.tolist(), counts.tolist()):
        if c == 1:
            ys, xs = np.where(g == v)
            return int(ys[0]), int(xs[0])
    return g.shape[0] // 2, g.shape[1] // 2

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    y, x = _find_marker(g)
    cy, cx = y + 2 * DR, x + 2 * DC
    out = np.zeros((3, 3), dtype=int)
    for i in range(3):
        for j in range(3):
            r, c = cy - 1 + i, cx - 1 + j
            if 0 <= r < H and 0 <= c < W:
                out[i, j] = g[r, c]
    return out.tolist()
''' % (marker, dr, dc)
    return src

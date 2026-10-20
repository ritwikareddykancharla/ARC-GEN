def build_program(d4, palette):
    bg = int(palette[0])
    shape_col = int(palette[8])
    src = '''import numpy as np

BG = %d
SHAPE = %d

def _ncols(h):
    return len(set(h[h != BG].tolist()))

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    if W >= H:
        n = H
        halves = [g[:, :n], g[:, n:2 * n]]
    else:
        n = W
        halves = [g[:n, :], g[n:2 * n, :]]
    has0 = bool((halves[0] == SHAPE).any())
    has1 = bool((halves[1] == SHAPE).any())
    if has0 and not has1:
        si = 0
    elif has1 and not has0:
        si = 1
    else:
        si = 0 if _ncols(halves[0]) <= _ncols(halves[1]) else 1
    shape = halves[si] != BG
    pattern = halves[1 - si]
    out = np.full((n * n, n * n), BG, dtype=int)
    for r in range(n):
        for c in range(n):
            col = int(pattern[r, c])
            if col != BG:
                block = out[r * n:(r + 1) * n, c * n:(c + 1) * n]
                block[shape] = col
    return out.tolist()
''' % (bg, shape_col)
    return src

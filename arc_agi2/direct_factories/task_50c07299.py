def build_program(d4, palette):
    # Original mechanism: the line extends in direction (dy, dx) = (-1, +1), i.e. up-right.
    dy, dx = -1, 1
    # D4 action on direction vectors: first optional row-reversal (x -> W-1-x), then clockwise rotations.
    if d4 >= 4:
        dx = -dx
    for _ in range(d4 % 4):
        # clockwise rotation: (y, x) -> (x, H-1-y)  => direction (dy, dx) -> (dx, -dy)
        dy, dx = dx, -dy
    bg_c = int(palette[7])
    line_c = int(palette[2])
    prog = '''import numpy as np
from collections import Counter

DY = %d
DX = %d
BG_DEFAULT = %d
LINE_DEFAULT = %d

def _background(g):
    vals = g.ravel().tolist()
    cnt = Counter(vals)
    best = cnt.most_common()
    top = best[0][1]
    cands = [c for c, k in best if k == top]
    if BG_DEFAULT in cands:
        return BG_DEFAULT
    return int(cands[0])

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = _background(g)
    ys, xs = np.nonzero(g != bg)
    cells = [(int(y), int(x)) for y, x in zip(ys, xs)]
    out = g.copy()
    if not cells:
        return out.tolist()
    n = len(cells)
    # leading end of the diagonal = the cell furthest along the travel direction
    ey, ex = max(cells, key=lambda c: (DY * c[0] + DX * c[1], -c[0], -c[1]))
    col = int(g[ey, ex])
    for y, x in cells:
        out[y, x] = bg
    for k in range(1, n + 2):
        y = ey + DY * k
        x = ex + DX * k
        if 0 <= y < H and 0 <= x < W:
            out[y, x] = col
    return out.tolist()
''' % (dy, dx, bg_c, line_c)
    return prog

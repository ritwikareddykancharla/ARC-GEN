def build_program(d4, palette):
    bg = int(palette[0])
    ring = int(palette[4])
    src = '''import numpy as np
from collections import Counter

BG = %d
RING = %d

def _full_lines(g, bg):
    H, W = g.shape
    rows = [y for y in range(H) if np.all(g[y, :] != bg)]
    cols = [x for x in range(W) if np.all(g[:, x] != bg)]
    return rows, cols

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    rows, cols = _full_lines(g, BG)
    if not rows or not cols:
        bg2 = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
        rows, cols = _full_lines(g, bg2)
    if not rows or not cols:
        return g.tolist()
    cy, cx = rows[0], cols[0]
    out = g.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            y, x = cy + dy, cx + dx
            if 0 <= y < H and 0 <= x < W:
                out[y, x] = RING
    return out.tolist()
''' % (bg, ring)
    return src

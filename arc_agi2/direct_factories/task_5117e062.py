def build_program(d4, palette):
    bg = int(palette[0])
    marker = int(palette[8])
    code = '''import numpy as np
from collections import Counter

BG = %d
MARKER = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    ys, xs = np.where(g == MARKER)
    if len(ys) == 0:
        return g.tolist()
    cy, cx = int(ys[0]), int(xs[0])
    y0, x0 = max(cy - 1, 0), max(cx - 1, 0)
    y1, x1 = min(cy + 1, H - 1), min(cx + 1, W - 1)
    win = g[y0:y1 + 1, x0:x1 + 1].copy()
    vals = [int(v) for v in win.ravel() if v != BG and v != MARKER]
    if vals:
        cnt = Counter(vals)
        best = max(cnt.values())
        col = min(c for c, n in cnt.items() if n == best)
    else:
        col = BG
    win[win == MARKER] = col
    return win.tolist()
''' % (bg, marker)
    return code

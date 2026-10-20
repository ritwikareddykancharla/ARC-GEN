def build_program(d4, palette):
    # The mechanism is D4-equivariant: every dot that is aligned with the rectangle,
    # on any of its four sides, shoots a line toward the rectangle. Colour roles are
    # inferred from the pixels, so no constants need specializing; d4 and palette are
    # accepted but the emitted program works directly in visible coordinates.
    prog = '''
import numpy as np
from collections import Counter

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    cnt = Counter(g.ravel().tolist())
    bg = cnt.most_common(1)[0][0]
    best = None
    for col, n in cnt.items():
        if col == bg:
            continue
        ys, xs = np.nonzero(g == col)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        if (y1 - y0 + 1) * (x1 - x0 + 1) == n:
            if best is None or n > best[0]:
                best = (n, col, int(y0), int(x0), int(y1), int(x1))
    out = g.copy()
    if best is None:
        return out.tolist()
    _, boxc, y0, x0, y1, x1 = best
    dys, dxs = np.nonzero((g != bg) & (g != boxc))
    for y, x in zip(dys.tolist(), dxs.tolist()):
        c = int(g[y, x])
        if x0 <= x <= x1:
            if y < y0:
                out[y + 1:y0, x] = c
            elif y > y1:
                out[y1 + 1:y, x] = c
        elif y0 <= y <= y1:
            if x < x0:
                out[y, x + 1:x0] = c
            elif x > x1:
                out[y, x1 + 1:x] = c
    return out.tolist()
'''
    return prog

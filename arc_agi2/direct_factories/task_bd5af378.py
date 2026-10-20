def build_program(d4, palette):
    fill = int(palette[8])
    src = '''import numpy as np
from collections import Counter

FILL = %d


def _find_corner(g):
    H, W = g.shape
    best = None
    for cy in (0, H - 1):
        for cx in (0, W - 1):
            c = g[cy, cx]
            if (g[cy, :] == c).all() and (g[:, cx] == c).all():
                rest = g[g != c]
                if rest.size > 0:
                    score = int(rest.size)
                    if best is None or score > best[0]:
                        best = (score, cy, cx)
    if best is None:
        return None
    return best[1], best[2]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    corner = _find_corner(g)
    if corner is None:
        bg = Counter(g.ravel().tolist()).most_common(1)[0][0]
        others = [c for c in np.unique(g).tolist() if c != bg]
        if not others:
            return g.tolist()
        L = others[0]
        rows = [y for y in range(H) if (g[y] == L).all()]
        cols = [x for x in range(W) if (g[:, x] == L).all()]
        if not rows or not cols:
            return g.tolist()
        cy, cx = rows[0], cols[0]
    else:
        cy, cx = corner
        L = int(g[cy, cx])
        rest = g[g != L].ravel().tolist()
        bg = Counter(rest).most_common(1)[0][0]
    ys, xs = np.indices((H, W))
    a = np.abs(ys - cy)
    b = np.abs(xs - cx)
    m = np.minimum(a, b)
    out = np.full((H, W), bg, dtype=int)
    off = a != b
    out[(m == 1) & off] = L
    out[(m >= 2) & off] = FILL
    diag = a == b
    out[diag & (a <= 1)] = FILL
    out[diag & (a >= 2)] = bg
    return out.tolist()
''' % fill
    return src

def build_program(d4, palette):
    marker = int(palette[4])
    bg = int(palette[0])
    src = '''import numpy as np

MARKER = %d
BG = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    if g.ndim != 2 or g.size == 0:
        return out.tolist()
    ys, xs = np.where(g == MARKER)
    if len(ys) == 0:
        return out.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    tmpl = g[y0:y1 + 1, x0:x1 + 1].copy()
    th, tw = tmpl.shape
    slot = tmpl == MARKER
    fixed = ~slot
    H, W = g.shape
    for y in range(H - th + 1):
        for x in range(W - tw + 1):
            if y == y0 and x == x0:
                continue
            win = g[y:y + th, x:x + tw]
            if not np.array_equal(win[fixed], tmpl[fixed]):
                continue
            if not np.all(win[slot] == BG):
                continue
            sub = out[y:y + th, x:x + tw]
            sub[slot] = MARKER
    return out.tolist()
''' % (marker, bg)
    return src

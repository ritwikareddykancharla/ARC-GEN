def build_program(d4, palette):
    bg = int(palette[0])
    frame = int(palette[5])
    src = '''import numpy as np

BG = %d
FRAME = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    ys, xs = np.where(g == FRAME)
    if ys.size == 0:
        return out.tolist()
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    if y1 - y0 < 2 or x1 - x0 < 2:
        return out.tolist()
    inner = g[y0 + 1:y1, x0 + 1:x1]
    # The two swap colours are the scene's non-background, non-frame colours.
    # Read them from the whole grid, because a colour can be missing from the interior.
    cols = sorted(set(np.unique(g).tolist()) - {BG, FRAME})
    if len(cols) != 2:
        cols = sorted(set(np.unique(inner).tolist()) - {BG, FRAME})
    if len(cols) == 2:
        a, b = cols
        new = inner.copy()
        new[inner == a] = b
        new[inner == b] = a
        out[y0 + 1:y1, x0 + 1:x1] = new
    return out.tolist()
''' % (bg, frame)
    return src

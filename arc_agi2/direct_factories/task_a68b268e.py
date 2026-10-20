def build_program(d4, palette):
    bg = int(palette[0])
    div = int(palette[1])
    priority = [int(palette[7]), int(palette[4]), int(palette[8]), int(palette[6])]
    src = '''import numpy as np
from collections import Counter

BG = %d
DIV = %d
# Highest priority first: original colours 7 > 4 > 8 > 6 under the episode palette.
PRIORITY = %r


def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out


def _panel_colour(p):
    vals = [int(v) for v in p.ravel().tolist() if v != BG and v != DIV]
    if not vals:
        return None
    return Counter(vals).most_common(1)[0][0]


def _rank(c):
    if c is None:
        return len(PRIORITY) + 1
    if c in PRIORITY:
        return PRIORITY.index(c)
    return len(PRIORITY)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # Divider lines: full rows / full columns made entirely of the divider colour.
    rcuts = [y for y in range(H) if (g[y, :] == DIV).all()]
    ccuts = [x for x in range(W) if (g[:, x] == DIV).all()]
    ys = _spans(rcuts, H)
    xs = _spans(ccuts, W)
    panels = [g[y0:y1 + 1, x0:x1 + 1] for (y0, y1) in ys for (x0, x1) in xs]
    if not panels:
        return g.tolist()
    shape = Counter([p.shape for p in panels]).most_common(1)[0][0]
    panels = [p for p in panels if p.shape == shape]
    # Paint lowest priority first so higher-priority colours end on top.
    panels.sort(key=lambda p: -_rank(_panel_colour(p)))
    out = np.full(shape, BG, dtype=int)
    for p in panels:
        m = (p != BG) & (p != DIV)
        out[m] = p[m]
    return out.tolist()
''' % (bg, div, priority)
    return src

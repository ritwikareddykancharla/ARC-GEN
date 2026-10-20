def build_program(d4, palette):
    k = int(d4) % 4
    # Track the original 'up' direction (-1,0) through the D4 map.
    # A row flip (d4>=4) leaves vertical vectors unchanged. Each clockwise turn maps (dr,dc)->(dc,-dr).
    # k=0: up, k=1: right, k=2: down, k=3: left.
    axis_rows = k in (0, 2)
    prefer_low = k in (0, 3)
    bg = int(palette[0])
    src = '''import numpy as np

AXIS_ROWS = %r
PREFER_LOW = %r
BG = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    pts = [(r, c, int(g[r, c])) for r in range(H) for c in range(W) if g[r, c] != BG]
    if not pts:
        return out.tolist()
    if AXIS_ROWS:
        seeds = sorted((r, c, col) for r, c, col in pts)
        L = H
    else:
        seeds = sorted((c, r, col) for r, c, col in pts)
        L = W

    def line(t, colour):
        if AXIS_ROWS:
            out[t, :] = colour
        else:
            out[:, t] = colour

    def side(t, colour):
        if AXIS_ROWS:
            out[t, 0] = colour
            out[t, W - 1] = colour
        else:
            out[0, t] = colour
            out[H - 1, t] = colour

    # full lines through each seed, across the grid
    for t, _, colr in seeds:
        line(t, colr)
    # border bands perpendicular to the lines: nearest seed along the axis,
    # with an equidistant tie going to the seed on the preferred side
    for t in range(L):
        best = None
        for s, _, colr in seeds:
            key = (abs(t - s), s if PREFER_LOW else -s)
            if best is None or key < best[0]:
                best = (key, colr)
        side(t, best[1])
    # caps: the two edge lines take the colours of the extreme seeds
    line(0, seeds[0][2])
    line(L - 1, seeds[-1][2])
    return out.tolist()
''' % (axis_rows, prefer_low, bg)
    return src

def build_program(d4, palette):
    bg = int(palette[0])
    bracket = int(palette[2])
    mover = int(palette[5])
    src = '''import numpy as np

BG = __BG__
BRACKET = __BR__
MOVER = __MV__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    red = (g == BRACKET)
    if not red.any():
        return out.tolist()
    # Each spine is a full line of the bracket. It holds wide >= 5 cells.
    # A perpendicular line holds at most 4 bracket cells.
    rc = red.sum(axis=1)
    cc = red.sum(axis=0)
    if int(rc.max()) >= int(cc.max()):
        horizontal = True
        m = int(rc.max())
        spines = [int(i) for i in np.nonzero(rc == m)[0]]
    else:
        horizontal = False
        m = int(cc.max())
        spines = [int(i) for i in np.nonzero(cc == m)[0]]
    # Movers are every non-background cell that is not bracket colour.
    movers = (g != BG) & (~red)
    pts = [(int(y), int(x)) for y, x in np.argwhere(movers)]
    out[movers] = BG
    for y, x in pts:
        c = y if horizontal else x
        best = None
        for s in sorted(spines):
            d = abs(s - c)
            if best is None or d < best[0]:
                best = (d, s)
        s = best[1]
        nc = 2 * s - c
        if horizontal:
            ny, nx = nc, x
        else:
            ny, nx = y, nc
        if 0 <= ny < H and 0 <= nx < W:
            out[ny, nx] = g[y, x]
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg)).replace('__BR__', str(bracket)).replace('__MV__', str(mover))
    return src

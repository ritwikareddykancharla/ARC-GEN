def build_program(d4, palette):
    bg = int(palette[0])
    ca = int(palette[3])
    cb = int(palette[6])
    src = '''import numpy as np

BG = %d
CA = %d
CB = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    ys, xs = np.nonzero(g != BG)
    if len(ys) == 0:
        return g.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    h, w = y1 - y0 + 1, x1 - x0 + 1
    vals, cnts = np.unique(g[y0:y1 + 1, x0:x1 + 1][g[y0:y1 + 1, x0:x1 + 1] != BG], return_counts=True)
    col = int(vals[int(np.argmax(cnts))])
    if col == CA:
        other = CB
    elif col == CB:
        other = CA
    else:
        other = CB if CB != BG else CA
    out = g.copy()
    # Each next piece is the previous piece transposed (h<->w), colour swapped,
    # placed so its corner diagonally touches the outward corner of the previous one.
    for dy, dx in ((1, 1), (-1, -1), (-1, 1), (1, -1)):
        r, c, ph, pw, pc = y0, x0, h, w, col
        for _ in range(200):
            nh, nw = pw, ph
            nr = r + ph if dy > 0 else r - nh
            nc = c + pw if dx > 0 else c - nw
            npc = other if pc == col else col
            if nr >= H or nc >= W or nr + nh <= 0 or nc + nw <= 0:
                break
            ra, rb = max(nr, 0), min(nr + nh, H)
            ca_, cb_ = max(nc, 0), min(nc + nw, W)
            out[ra:rb, ca_:cb_] = npc
            r, c, ph, pw, pc = nr, nc, nh, nw, npc
    return out.tolist()
''' % (bg, ca, cb)
    return src

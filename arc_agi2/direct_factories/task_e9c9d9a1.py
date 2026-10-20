def build_program(d4, palette):
    k = int(d4) % 4
    flip = int(d4) >= 4

    def tf(r, c):
        # r, c are unit-square corner indices (0 = top/left, 1 = bottom/right)
        if flip:
            c = 1 - c
        for _ in range(k):
            # clockwise rotation: old (r, c) -> new (c, n-1-r)
            r, c = c, 1 - r
        return r, c

    orig_corners = {(0, 0): 2, (0, 1): 4, (1, 0): 1, (1, 1): 8}
    vis = {}
    for (r, c), col in orig_corners.items():
        vis[tf(r, c)] = int(palette[col])
    line = int(palette[3])
    inner = int(palette[7])
    tl = vis[(0, 0)]
    tr = vis[(0, 1)]
    bl = vis[(1, 0)]
    br = vis[(1, 1)]

    prog = '''import numpy as np

LINE = %d
INNER = %d
C_TL = %d
C_TR = %d
C_BL = %d
C_BR = %d

def _intervals(divs, n):
    res = []
    start = 0
    for d in list(divs) + [n]:
        if d > start:
            res.append((start, d - 1))
        start = d + 1
    return res

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    rows_div = [y for y in range(H) if np.all(g[y] == LINE)]
    cols_div = [x for x in range(W) if np.all(g[:, x] == LINE)]
    R = _intervals(rows_div, H)
    C = _intervals(cols_div, W)
    nr, nc = len(R), len(C)
    if nr == 0 or nc == 0:
        return g.tolist()

    def fill(i, j, col):
        (y0, y1), (x0, x1) = R[i], C[j]
        g[y0:y1 + 1, x0:x1 + 1] = col

    # interior cells: neither first/last cell-row nor first/last cell-column
    for i in range(1, nr - 1):
        for j in range(1, nc - 1):
            fill(i, j, INNER)
    # visible corner cells, colours specialised for this orientation/palette
    fill(0, 0, C_TL)
    fill(0, nc - 1, C_TR)
    fill(nr - 1, 0, C_BL)
    fill(nr - 1, nc - 1, C_BR)
    return g.tolist()
''' % (line, inner, tl, tr, bl, br)
    return prog

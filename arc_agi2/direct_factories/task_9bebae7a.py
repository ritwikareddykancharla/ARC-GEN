def build_program(d4, palette):
    bg = int(palette[0])
    fig = int(palette[4])
    mk = int(palette[6])
    # Rotations keep the chirality of the arm->mirror relation; reflections invert it.
    ccw = 1 if int(d4) < 4 else 0
    src = '''import numpy as np

BG = %d
FIG = %d
MK = %d
CCW = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    pm = g == MK
    out[pm] = BG
    if not pm.any():
        return out.tolist()
    cells = [(int(r), int(c)) for r, c in zip(*np.nonzero(pm))]
    S = set(cells)
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def deg(cell):
        r, c = cell
        return sum(1 for a, b in dirs if (r + a, c + b) in S)

    junction = max(cells, key=lambda cl: (deg(cl), -cl[0], -cl[1]))
    best = None
    bestlen = -1
    for a, b in dirs:
        n = 0
        r, c = junction
        while (r + a * (n + 1), c + b * (n + 1)) in S:
            n += 1
        if n > bestlen:
            bestlen = n
            best = (a, b)
    ady, adx = best
    if CCW:
        mdy, mdx = -adx, ady
    else:
        mdy, mdx = adx, -ady
    fm = g == FIG
    if not fm.any():
        return out.tolist()
    ys, xs = np.nonzero(fm)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    bm = fm[y0:y1 + 1, x0:x1 + 1]
    h, w = bm.shape
    if mdx != 0:
        bm = bm[:, ::-1]
        ny = y0
        nx = x1 + 1 if mdx > 0 else x0 - w
    else:
        bm = bm[::-1, :]
        nx = x0
        ny = y1 + 1 if mdy > 0 else y0 - h
    for i in range(h):
        for j in range(w):
            if bm[i, j]:
                yy, xx = ny + i, nx + j
                if 0 <= yy < H and 0 <= xx < W:
                    out[yy, xx] = FIG
    return out.tolist()
''' % (bg, fig, mk, ccw)
    return src

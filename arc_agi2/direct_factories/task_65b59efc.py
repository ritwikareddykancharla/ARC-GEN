TEMPLATE = '''import numpy as np

BG = @BG@
SEP = @SEP@
BAND_AXIS = @BAX@
COL_AXIS = @CAX@
BAND_REV = @BREV@
COL_REV = @CREV@


def _span(lo, hi, n, rev):
    lo = max(0, min(lo, n))
    hi = max(lo, min(hi, n))
    if rev:
        return n - hi, n - lo
    return lo, hi


def _region(g, blo, bhi, clo, chi):
    b0, b1 = _span(blo, bhi, g.shape[BAND_AXIS], BAND_REV)
    c0, c1 = _span(clo, chi, g.shape[COL_AXIS], COL_REV)
    return g[@SLICE@]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    nb = g.shape[BAND_AXIS]
    nc = g.shape[COL_AXIS]
    edge = _region(g, 0, 1, 0, nc).ravel()@ORDER@
    hits = np.where(edge == SEP)[0]
    if hits.size == 0 or int(hits[0]) < 1:
        return [[int(v) for v in row] for row in g]
    k = int(hits[0])
    p = k + 1
    motifs = {}
    n = 0
    while n * p + k <= nc:
        x0 = n * p
        top = _region(g, 0, k, x0, x0 + k)
        if top.shape != (k, k):
            break
        vals = top[(top != BG) & (top != SEP)]
        if vals.size == 0:
            break
        c = int(np.bincount(vals).argmax())
        strip = _region(g, 2 * p, nb, x0, x0 + k)
        pv = strip[(strip != BG) & (strip != SEP)]
        paint = int(np.bincount(pv).argmax()) if pv.size else BG
        if c not in motifs:
            motifs[c] = (top == c, paint)
        n += 1
    out = np.full((k * k, k * k), BG, dtype=int)
    for j in range(n):
        x0 = j * p
        mid = _region(g, p, p + k, x0, x0 + k)
        for r in range(mid.shape[0]):
            for s in range(mid.shape[1]):
                c = int(mid[r, s])
                if c == BG or c == SEP or c not in motifs:
                    continue
                mask, paint = motifs[c]
                blk = out[r * k:(r + 1) * k, s * k:(s + 1) * k]
                blk[mask] = paint
    return out.tolist()
'''


def _step(axis, rev):
    # one clockwise rotation: new row = old col, new col = (H-1) - old row
    if axis == 0:
        return 1, not rev
    return 0, rev


def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(v) for v in palette]
    # canonical band axis (y) and canonical column axis (x) -> visible axis/reversal
    y_axis, y_rev = 0, False
    x_axis, x_rev = 1, False
    if d4 >= 4:
        x_rev = not x_rev
    for _ in range(d4 % 4):
        y_axis, y_rev = _step(y_axis, y_rev)
        x_axis, x_rev = _step(x_axis, x_rev)
    if x_axis == 1:
        slice_expr = 'b0:b1, c0:c1'
    else:
        slice_expr = 'c0:c1, b0:b1'
    src = TEMPLATE
    src = src.replace('@BG@', str(pal[0]))
    src = src.replace('@SEP@', str(pal[5]))
    src = src.replace('@BAX@', str(y_axis))
    src = src.replace('@CAX@', str(x_axis))
    src = src.replace('@BREV@', 'True' if y_rev else 'False')
    src = src.replace('@CREV@', 'True' if x_rev else 'False')
    src = src.replace('@SLICE@', slice_expr)
    src = src.replace('@ORDER@', '[::-1]' if x_rev else '')
    return src

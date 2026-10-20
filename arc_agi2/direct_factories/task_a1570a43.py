def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    green = int(palette[3])
    src = '''import numpy as np

BG = %d
SHAPE = %d
MARK = %d


def _roles(g):
    vals, counts = np.unique(g, return_counts=True)
    present = dict(zip(vals.tolist(), counts.tolist()))
    bg, shape, mark = BG, SHAPE, MARK
    if bg not in present or shape not in present or mark not in present:
        bg = int(vals[np.argmax(counts)])
        others = sorted([(c, v) for v, c in present.items() if v != bg])
        if len(others) < 2:
            return None
        mark = others[0][1]
        shape = others[-1][1]
    return bg, shape, mark


def _place(lo, hi, a0, a1):
    # lo/hi are marker lines; the interior is strictly between them.
    inner = hi - lo - 1
    size = a1 - a0 + 1
    start = lo + 1
    if size == inner:
        return start
    if a0 > lo and a1 < hi:
        return a0
    if size > inner:
        return start + (inner - size) // 2
    if a0 <= lo:
        return start
    return hi - size


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    roles = _roles(g)
    if roles is None:
        return g.tolist()
    bg, shape, mark = roles
    my, mx = np.nonzero(g == mark)
    sy, sx = np.nonzero(g == shape)
    if len(my) == 0 or len(sy) == 0:
        return g.tolist()
    r0, r1 = int(my.min()), int(my.max())
    c0, c1 = int(mx.min()), int(mx.max())
    y0, y1 = int(sy.min()), int(sy.max())
    x0, x1 = int(sx.min()), int(sx.max())
    ny = _place(r0, r1, y0, y1)
    nx = _place(c0, c1, x0, x1)
    H, W = g.shape
    out = g.copy()
    out[g == shape] = bg
    for y, x in zip(sy.tolist(), sx.tolist()):
        yy = y - y0 + ny
        xx = x - x0 + nx
        if 0 <= yy < H and 0 <= xx < W:
            out[yy, xx] = shape
    return out.tolist()
''' % (bg, red, green)
    return src

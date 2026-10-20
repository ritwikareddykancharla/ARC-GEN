TEMPLATE = '''import numpy as np

HORIZONTAL = __HORIZONTAL__
CORNER = __CORNER__
BG = __BG__


def _layout(av, bv, cv, first_c, L, C):
    half = L // 2
    bmin = min(bv)
    bs = [b - bmin for b in bv]
    fa = [a for a, c in zip(av, cv) if c == first_c]
    sa = [a for a, c in zip(av, cv) if c != first_c]
    if fa and sa:
        if max(fa) < min(sa):
            order = [1, -1]
        elif min(fa) > max(sa):
            order = [-1, 1]
        elif sum(fa) / len(fa) <= sum(sa) / len(sa):
            order = [1, -1]
        else:
            order = [-1, 1]
    else:
        order = [1, -1]
    for sgn in order:
        ap = [sgn * a for a in av]
        lo, hi = min(ap), max(ap)
        cands = [lo, hi - (L - 1)] + list(range(hi - (L - 1), lo + 1))
        for t in cands:
            aa = [x - t for x in ap]
            if min(aa) < 0 or max(aa) > L - 1:
                continue
            if all((x < half) == (c == first_c) for x, c in zip(aa, cv)):
                return list(zip(aa, bs, cv))
    sgn = order[0]
    ap = [sgn * a for a in av]
    lo = min(ap)
    return [(x - lo, b, c) for x, b, c in zip(ap, bs, cv)]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    ys, xs = np.where(g == CORNER)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    out = g[y0:y1 + 1, x0:x1 + 1].copy()
    out[1:-1, 1:-1] = BG
    H, W = out.shape
    if HORIZONTAL:
        first_c = int(g[y0 + 1, x0])
        L, C = W - 2, H - 2
    else:
        first_c = int(g[y0, x0 + 1])
        L, C = H - 2, W - 2
    mask = (g != BG) & (g != CORNER)
    mask[y0:y1 + 1, x0:x1 + 1] = False
    sy, sx = np.where(mask)
    if len(sy) == 0:
        return out.tolist()
    cv = [int(g[y, x]) for y, x in zip(sy, sx)]
    if HORIZONTAL:
        av = [int(x) for x in sx]
        bv = [int(y) for y in sy]
    else:
        av = [int(y) for y in sy]
        bv = [int(x) for x in sx]
    for a, b, c in _layout(av, bv, cv, first_c, L, C):
        if HORIZONTAL:
            r, q = 1 + b, 1 + a
        else:
            r, q = 1 + a, 1 + b
        if 1 <= r <= H - 2 and 1 <= q <= W - 2:
            out[r, q] = c
    return out.tolist()
'''


def build_program(d4, palette):
    horizontal = (int(d4) % 2 == 0)
    corner = int(palette[4])
    bg = int(palette[0])
    src = TEMPLATE
    src = src.replace('__HORIZONTAL__', 'True' if horizontal else 'False')
    src = src.replace('__CORNER__', str(corner))
    src = src.replace('__BG__', str(bg))
    return src

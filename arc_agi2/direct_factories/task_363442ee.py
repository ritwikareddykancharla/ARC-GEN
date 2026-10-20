def _fwd(r, c, H, W, d4):
    if d4 >= 4:
        c = W - 1 - c
    for _ in range(d4 % 4):
        r, c = c, H - 1 - r
        H, W = W, H
    return r, c, H, W


def build_program(d4, palette):
    d4 = int(d4)
    gray = int(palette[5])
    blue = int(palette[1])
    r, c, Hv, Wv = _fwd(0, 0, 9, 13, d4)
    vertical = (d4 % 4) % 2 == 0
    if vertical:
        first_along = (r == 0)
        low_side = (c == 0)
    else:
        first_along = (c == 0)
        low_side = (r == 0)
    src = '''import numpy as np

DIV_VERTICAL = %r
TPL_FIRST_ALONG = %r
TPL_LOW_SIDE = %r
GRAY = %d
BLUE = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    if DIV_VERTICAL:
        cand = [x for x in range(W) if (g[:, x] == GRAY).all()]
        if cand:
            d = min(cand) if TPL_LOW_SIDE else max(cand)
        else:
            s0 = max(1, H // 3)
            d = s0 if TPL_LOW_SIDE else W - 1 - s0
        if TPL_LOW_SIDE:
            s = d
            c0 = 0
            far_lo, far_hi = d + 1, W - 1
        else:
            s = W - 1 - d
            c0 = d + 1
            far_lo, far_hi = 0, d - 1
        if s <= 0:
            return out.tolist()
        r0 = 0 if TPL_FIRST_ALONG else H - s
        tpl = g[r0:r0 + s, c0:c0 + s].copy()
        th, tw = tpl.shape
        cy, cx = th // 2, tw // 2
        markers = [(y, x) for y in range(H) for x in range(far_lo, far_hi + 1) if g[y, x] == BLUE]
        for y, x in markers:
            for dy in range(th):
                for dx in range(tw):
                    yy, xx = y - cy + dy, x - cx + dx
                    if 0 <= yy < H and far_lo <= xx <= far_hi:
                        out[yy, xx] = tpl[dy, dx]
    else:
        cand = [y for y in range(H) if (g[y, :] == GRAY).all()]
        if cand:
            d = min(cand) if TPL_LOW_SIDE else max(cand)
        else:
            s0 = max(1, W // 3)
            d = s0 if TPL_LOW_SIDE else H - 1 - s0
        if TPL_LOW_SIDE:
            s = d
            r0 = 0
            far_lo, far_hi = d + 1, H - 1
        else:
            s = H - 1 - d
            r0 = d + 1
            far_lo, far_hi = 0, d - 1
        if s <= 0:
            return out.tolist()
        c0 = 0 if TPL_FIRST_ALONG else W - s
        tpl = g[r0:r0 + s, c0:c0 + s].copy()
        th, tw = tpl.shape
        cy, cx = th // 2, tw // 2
        markers = [(y, x) for y in range(far_lo, far_hi + 1) for x in range(W) if g[y, x] == BLUE]
        for y, x in markers:
            for dy in range(th):
                for dx in range(tw):
                    yy, xx = y - cy + dy, x - cx + dx
                    if far_lo <= yy <= far_hi and 0 <= xx < W:
                        out[yy, xx] = tpl[dy, dx]
    return out.tolist()
''' % (vertical, first_along, low_side, gray, blue)
    return src

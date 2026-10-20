def build_program(d4, palette):
    d4 = int(d4) % 8
    bg_default = int(palette[7])

    def fwd(r, c, H, W):
        if d4 >= 4:
            c = W - 1 - c
        for _ in range(d4 % 4):
            r, c = c, H - 1 - r
            H, W = W, H
        return r, c

    frames = []
    for (r0, c0) in ((2, 2), (8, 8)):
        a = fwd(r0, c0, 15, 15)
        b = fwd(r0 + 4, c0 + 4, 15, 15)
        frames.append((min(a[0], b[0]), min(a[1], b[1])))

    rows = (0, False)
    cols = (1, False)
    if d4 >= 4:
        cols = (1, True)
    for _ in range(d4 % 4):
        rows, cols = cols, (rows[0], not rows[1])
    row_low = not rows[1]
    col_low = not cols[1]

    template = """import numpy as np

BG_DEFAULT = __BG__
FRAMES = __FRAMES__
ROW_LOW = __ROWLOW__
COL_LOW = __COLLOW__


def _place(s, L, n, low):
    if L >= 3:
        return 0
    if L == 1:
        prefs = [1, 0, 2]
    else:
        prefs = [0, 1] if low else [1, 0]
    for p in prefs:
        t = s - p
        if t >= 0 and t + 3 <= n:
            return p
    return prefs[0]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = int(g[0, 0]) if H > 0 and W > 0 else BG_DEFAULT
    if W >= 3:
        fc = int(g[0, 1])
    elif H >= 3:
        fc = int(g[1, 0])
    else:
        fc = bg
    inner = g[1:-1, 1:-1]
    motif = np.full((3, 3), bg, dtype=int)
    if inner.size > 0:
        mask = inner != bg
        if mask.any():
            ys, xs = np.where(mask)
            y0, y1 = int(ys.min()), int(ys.max())
            x0, x1 = int(xs.min()), int(xs.max())
            sub = inner[y0:y1 + 1, x0:x1 + 1][:3, :3]
            h, w = sub.shape
            oy = _place(y0, h, inner.shape[0], ROW_LOW)
            ox = _place(x0, w, inner.shape[1], COL_LOW)
            motif[oy:oy + h, ox:ox + w] = sub
    out = np.full((15, 15), bg, dtype=int)
    for (y, x) in FRAMES:
        out[y, x + 1:x + 4] = fc
        out[y + 4, x + 1:x + 4] = fc
        out[y + 1:y + 4, x] = fc
        out[y + 1:y + 4, x + 4] = fc
        out[y + 1:y + 4, x + 1:x + 4] = motif
    return out.tolist()
"""
    prog = template.replace('__BG__', repr(bg_default))
    prog = prog.replace('__FRAMES__', repr(frames))
    prog = prog.replace('__ROWLOW__', repr(bool(row_low)))
    prog = prog.replace('__COLLOW__', repr(bool(col_low)))
    return prog

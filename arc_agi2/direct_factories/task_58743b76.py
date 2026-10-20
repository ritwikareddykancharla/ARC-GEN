def build_program(d4, palette):
    bg = int(palette[0])
    bar = int(palette[8])
    src = '''import numpy as np

BG = %d
BAR = %d

def _bbox(mask):
    pts = np.argwhere(mask)
    if len(pts) == 0:
        return None
    y0, x0 = pts.min(0)
    y1, x1 = pts.max(0)
    return int(y0), int(x0), int(y1), int(x1)

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    is_bar = (g == BAR)
    # Bar rows are almost entirely the bar colour; canvas rows hold only 2 bar cells.
    bar_rows = [r for r in range(H) if 2 * int(is_bar[r, :].sum()) > W]
    bar_cols = [c for c in range(W) if 2 * int(is_bar[:, c].sum()) > H]
    can_rows = [r for r in range(H) if r not in bar_rows]
    can_cols = [c for c in range(W) if c not in bar_cols]
    if len(bar_rows) == 2 and len(bar_cols) == 2 and can_rows and can_cols:
        kr = sorted(bar_rows)
        kc = sorted(bar_cols)
        key = [[int(g[kr[i], kc[j]]) for j in range(2)] for i in range(2)]
        y0, y1 = min(can_rows), max(can_rows)
        x0, x1 = min(can_cols), max(can_cols)
    else:
        bb = _bbox(g == BG)
        if bb is None:
            return out.tolist()
        y0, x0, y1, x1 = bb
        inside = np.zeros_like(is_bar)
        inside[y0:y1 + 1, x0:x1 + 1] = True
        kb = _bbox((~is_bar) & (~inside))
        if kb is None:
            return out.tolist()
        ky0, kx0, ky1, kx1 = kb
        key = [[int(g[ky0, kx0]), int(g[ky0, kx1])], [int(g[ky1, kx0]), int(g[ky1, kx1])]]
    h = y1 - y0 + 1
    w = x1 - x0 + 1
    hh = h // 2
    hw = w // 2
    for y in range(y0, y1 + 1):
        qy = 0 if (y - y0) < hh else 1
        for x in range(x0, x1 + 1):
            v = g[y, x]
            if v == BG or v == BAR:
                continue
            qx = 0 if (x - x0) < hw else 1
            out[y, x] = key[qy][qx]
    return out.tolist()
''' % (bg, bar)
    return src

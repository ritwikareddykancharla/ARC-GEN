def build_program(d4, palette):
    bg = int(palette[0])
    wall = int(palette[8])
    template = '''import numpy as np
from collections import Counter

BG = __BG__
WALL = __WALL__


def _stamp(g, dot_mask, out, vertical, line, dot):
    H, W = g.shape
    changed = False
    if vertical:
        c = line
        for y in range(H):
            if g[y, c] != WALL:
                continue
            if c - 1 >= 0 and dot_mask[y, :c].any():
                out[y, c - 1] = dot
                changed = True
            if c + 1 < W and dot_mask[y, c + 1:].any():
                out[y, c + 1] = dot
                changed = True
    else:
        r = line
        for x in range(W):
            if g[r, x] != WALL:
                continue
            if r - 1 >= 0 and dot_mask[:r, x].any():
                out[r - 1, x] = dot
                changed = True
            if r + 1 < H and dot_mask[r + 1:, x].any():
                out[r + 1, x] = dot
                changed = True
    return changed


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = np.full_like(g, BG)
    out[g == WALL] = WALL
    wy, wx = np.where(g == WALL)
    if len(wy) == 0:
        return out.tolist()
    dot_mask = (g != BG) & (g != WALL)
    vals = g[dot_mask].tolist()
    if not vals:
        return out.tolist()
    dot = int(Counter(vals).most_common(1)[0][0])
    rows = Counter(wy.tolist())
    cols = Counter(wx.tolist())
    if len(cols) == 1 and len(rows) > 1:
        vertical = True
        line = int(wx[0])
    elif len(rows) == 1 and len(cols) > 1:
        vertical = False
        line = int(wy[0])
    elif len(rows) == 1 and len(cols) == 1:
        r = int(wy[0])
        c = int(wx[0])
        v_ok = not dot_mask[:, c].any()
        h_ok = not dot_mask[r, :].any()
        if v_ok != h_ok:
            vertical = v_ok
        else:
            tv = out.copy()
            th = out.copy()
            cv = _stamp(g, dot_mask, tv, True, c, dot)
            ch = _stamp(g, dot_mask, th, False, r, dot)
            if cv != ch:
                vertical = cv
            else:
                dv = abs(c - (W - 1) / 2.0)
                dh = abs(r - (H - 1) / 2.0)
                vertical = dv <= dh
        line = c if vertical else r
    else:
        bc, nc = cols.most_common(1)[0]
        br, nr = rows.most_common(1)[0]
        vertical = nc >= nr
        line = int(bc) if vertical else int(br)
    _stamp(g, dot_mask, out, vertical, line, dot)
    return out.tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__WALL__', str(wall))

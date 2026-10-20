def build_program(d4, palette):
    k = int(d4) % 8
    dr, dc = 0, 1
    if k >= 4:
        dc = -dc
    for _ in range(k % 4):
        dr, dc = dc, -dr
    bg = int(palette[7])
    mk = int(palette[6])
    if (dr, dc) == (0, 1):
        cell, nl, ln = '(lane, t)', 'H', 'W'
    elif (dr, dc) == (0, -1):
        cell, nl, ln = '(lane, W - 1 - t)', 'H', 'W'
    elif (dr, dc) == (1, 0):
        cell, nl, ln = '(t, lane)', 'W', 'H'
    else:
        cell, nl, ln = '(H - 1 - t, lane)', 'W', 'H'
    template = '''import numpy as np

BG = __BG__
MARK = __MK__
DR = __DR__
DC = __DC__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    NL = __NL__
    L = __LN__
    if L < 2 or NL < 3:
        return out.tolist()

    def cell(lane, t):
        return __CELL__

    def inside(r, c):
        return 0 <= r < H and 0 <= c < W

    def first_cell(lane):
        for t in range(1, L):
            v = int(g[cell(lane, t)])
            if v != BG:
                return t, v
        return None, None

    def opening(r, c, d):
        if not inside(r, c) or g[r, c] != BG:
            return False
        dy, dx = d
        a = (r + dx, c + dy)
        b = (r - dx, c - dy)
        if not inside(a[0], a[1]) or not inside(b[0], b[1]):
            return False
        va = int(g[a])
        vb = int(g[b])
        return va != BG and vb != BG and va == vb

    def walk(r, c):
        d = (DR, DC)
        for _ in range(4 * H * W):
            nr, nc = r + d[0], c + d[1]
            if inside(nr, nc) and g[nr, nc] == BG:
                r, c = nr, nc
                continue
            opts = []
            for nd in ((d[1], d[0]), (-d[1], -d[0])):
                if opening(r + nd[0], c + nd[1], nd):
                    opts.append(nd)
            if len(opts) != 1:
                break
            d = opts[0]
            r, c = r + d[0], c + d[1]
        return r, c

    released = []
    for lane in range(1, NL - 1):
        if g[cell(lane, 0)] != MARK or g[cell(lane, 1)] != BG:
            continue
        ta, ca = first_cell(lane - 1)
        tb, cb = first_cell(lane + 1)
        if ca is None or cb is None or ca != cb or ta != tb:
            continue
        if g[cell(lane, ta)] != BG:
            continue
        released.append(lane)
    ends = []
    for lane in released:
        r, c = cell(lane, 1)
        ends.append(walk(r, c))
    for lane in released:
        out[cell(lane, 0)] = BG
    for r, c in ends:
        out[r, c] = MARK
    return out.tolist()
'''
    src = template
    for key, val in (('__BG__', str(bg)), ('__MK__', str(mk)), ('__DR__', str(dr)), ('__DC__', str(dc)), ('__NL__', nl), ('__LN__', ln), ('__CELL__', cell)):
        src = src.replace(key, val)
    return src

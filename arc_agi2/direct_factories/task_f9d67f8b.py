TEMPLATE = '''import numpy as np

OCC = __OCC__
ROW_PREF = __ROWPREF__
COL_PREF = __COLPREF__


def _axis(g, size, cols, pref):
    found = []
    for a in range(1, size):
        ok = True
        for j in range(min(a, size - a)):
            p, q = a - 1 - j, a + j
            if cols:
                u, v = g[:, p], g[:, q]
            else:
                u, v = g[p, :], g[q, :]
            known = (u != OCC) & (v != OCC)
            if np.any(u[known] != v[known]):
                ok = False
                break
        if ok:
            found.append(a)
    if not found:
        return None

    def key(a):
        d = 2 * a - size
        return (abs(d), 0 if d * pref >= 0 else 1, a)
    return min(found, key=key)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    ax = _axis(g, W, True, COL_PREF)
    ay = _axis(g, H, False, ROW_PREF)

    def mirrors(y, x):
        res = []
        if ax is not None:
            res.append((y, 2 * ax - 1 - x))
        if ay is not None:
            res.append((2 * ay - 1 - y, x))
        if ax is not None and ay is not None:
            res.append((2 * ay - 1 - y, 2 * ax - 1 - x))
        return res

    out = g.copy()
    for y in range(H):
        for x in range(W):
            if g[y, x] != OCC:
                continue
            vals = set()
            for a, b in mirrors(y, x):
                if 0 <= a < H and 0 <= b < W and g[a, b] != OCC:
                    vals.add(int(g[a, b]))
            if len(vals) == 1:
                out[y, x] = vals.pop()
    if ax is None or ay is None:
        return out.tolist()
    partial = out.copy()
    for y in range(H):
        for x in range(W):
            if partial[y, x] != OCC:
                continue
            yy, xx = x + ay - ax, y + ax - ay
            cands = [(yy, xx)] + mirrors(yy, xx)
            vals = set()
            for a, b in cands:
                if 0 <= a < H and 0 <= b < W and partial[a, b] != OCC:
                    vals.add(int(partial[a, b]))
            if len(vals) == 1:
                out[y, x] = vals.pop()
    return out.tolist()
'''


def build_program(d4, palette):
    d = int(d4)
    k = d % 4
    rs, cs = 1, 1
    if d >= 4:
        cs = -cs
    for _ in range(k):
        rs, cs = cs, -rs
    occ = int(palette[9])
    return (TEMPLATE.replace('__OCC__', str(occ))
            .replace('__ROWPREF__', str(rs))
            .replace('__COLPREF__', str(cs)))

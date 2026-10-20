TEMPLATE = '''import numpy as np
from collections import Counter

HOLE = __HOLE__


def _row_period(g, known):
    H, W = g.shape
    for p in range(1, H + 1):
        ok = True
        for r in range(p):
            sub = g[r::p]
            km = known[r::p]
            for x in range(W):
                v = sub[km[:, x], x]
                if v.size > 1 and np.any(v != v[0]):
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return p
    return H


def _mirror(table, py, px, axis):
    n = py if axis == 0 else px
    for s in range(n):
        ok = True
        compared = 0
        for r in range(py):
            for c in range(px):
                if axis == 0:
                    rr, cc = (s - r) % py, c
                else:
                    rr, cc = r, (s - c) % px
                if (rr, cc) == (r, c):
                    continue
                a = table[r][c]
                b = table[rr][cc]
                if a is None or b is None:
                    continue
                compared += 1
                if a != b:
                    ok = False
                    break
            if not ok:
                break
        if ok and compared > 0:
            return s
    return None


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    known = g != HOLE
    if known.all() or not known.any():
        return g.tolist()
    py = _row_period(g, known)
    px = _row_period(g.T, known.T)
    table = [[None] * px for _ in range(py)]
    for r in range(py):
        for c in range(px):
            v = g[r::py, c::px][known[r::py, c::px]]
            if v.size:
                cnt = Counter(int(t) for t in v)
                best = max(cnt.values())
                table[r][c] = min(k for k, n in cnt.items() if n == best)
    if any(table[r][c] is None for r in range(py) for c in range(px)):
        sy = _mirror(table, py, px, 0)
        sx = _mirror(table, py, px, 1)
        for _ in range(4):
            changed = False
            for r in range(py):
                for c in range(px):
                    if table[r][c] is not None:
                        continue
                    cands = []
                    if sy is not None:
                        cands.append(((sy - r) % py, c))
                    if sx is not None:
                        cands.append((r, (sx - c) % px))
                    if sy is not None and sx is not None:
                        cands.append(((sy - r) % py, (sx - c) % px))
                    for rr, cc in cands:
                        if table[rr][cc] is not None:
                            table[r][c] = table[rr][cc]
                            changed = True
                            break
            if not changed:
                break
    out = g.copy()
    for y in range(H):
        for x in range(W):
            if not known[y, x]:
                v = table[y % py][x % px]
                if v is not None:
                    out[y, x] = v
    return out.tolist()
'''


def build_program(d4, palette):
    hole = int(palette[0])
    return TEMPLATE.replace('__HOLE__', repr(hole))

def build_program(d4, palette):
    k = d4 % 4
    rrev, crev = False, d4 >= 4
    for _ in range(k):
        rrev, crev = crev, (not rrev)
    bg = int(palette[4])
    block = int(palette[2])
    src = '''import numpy as np
from collections import deque

BG = __BG__
BLOCK = __BLOCK__
REV_R = __RR__
REV_C = __RC__


def _axis(n, s0, s, rev, b):
    m = n * s // s0
    if not rev:
        idx = [i * s0 // s for i in range(m)]
        b2 = b * s // s0
    else:
        idx = [n - 1 - ((m - 1 - i) * s0 // s) for i in range(m)]
        bo = n - (b + s0)
        b2 = m - (bo * s // s0 + s)
    return idx, b2


def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H0, W0 = g.shape
    rows = [y for y in range(H0) if g[y, 0] != BG and (g[y] == g[y, 0]).all()]
    cols = [x for x in range(W0) if g[0, x] != BG and (g[:, x] == g[0, x]).all()]
    if not rows or not cols:
        return out.tolist()

    def quad(y, x):
        return (sum(1 for r in rows if y > r), sum(1 for c in cols if x > c))

    tpl = None
    for (y0, y1) in _spans(rows, H0):
        for (x0, x1) in _spans(cols, W0):
            sub = g[y0:y1 + 1, x0:x1 + 1]
            if set(np.unique(sub).tolist()) - {BG, BLOCK}:
                tpl = (y0, x0, y1, x1)
                break
        if tpl is not None:
            break
    if tpl is None:
        return out.tolist()
    y0, x0, y1, x1 = tpl
    sub = g[y0:y1 + 1, x0:x1 + 1]
    ys, xs = np.where(sub != BG)
    P = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    two = np.argwhere(P == BLOCK)
    if len(two) == 0:
        return out.tolist()
    br, bc = int(two[:, 0].min()), int(two[:, 1].min())
    s0 = int(two[:, 0].max()) - br + 1
    tq = quad(y0, x0)
    ph, pw = P.shape
    for cells in _components(g == BLOCK):
        oy0 = min(c[0] for c in cells)
        ox0 = min(c[1] for c in cells)
        oy1 = max(c[0] for c in cells)
        q = quad(oy0, ox0)
        if q == tq:
            continue
        s = oy1 - oy0 + 1
        ridx, r2 = _axis(ph, s0, s, REV_R, br)
        cidx, c2 = _axis(pw, s0, s, REV_C, bc)
        if not ridx or not cidx:
            continue
        Q = P[np.ix_(ridx, cidx)]
        Hq, Wq = Q.shape
        if q[1] != tq[1]:
            Q = Q[:, ::-1]
            c2 = Wq - (c2 + s)
        if q[0] != tq[0]:
            Q = Q[::-1, :]
            r2 = Hq - (r2 + s)
        ty, tx = oy0 - r2, ox0 - c2
        for i in range(Hq):
            yy = ty + i
            if yy < 0 or yy >= H0:
                continue
            for j in range(Wq):
                xx = tx + j
                v = int(Q[i, j])
                if v != BG and 0 <= xx < W0:
                    out[yy, xx] = v
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg)).replace('__BLOCK__', str(block))
    src = src.replace('__RR__', 'True' if rrev else 'False').replace('__RC__', 'True' if crev else 'False')
    return src

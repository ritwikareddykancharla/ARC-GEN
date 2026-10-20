TEMPLATE = '''import numpy as np
from collections import Counter, deque

DN = @DN@
RT = @RT@
STRIPS = @STRIPS@
SY = @SY@
SX = @SX@


def _key(y, x):
    return (y * DN[0] + x * DN[1], y * RT[0] + x * RT[1])


def _background(g):
    cnt = Counter(int(v) for v in g.ravel())
    m = max(cnt.values())
    best = None
    bk = None
    h, w = g.shape
    for y in range(h):
        for x in range(w):
            v = int(g[y, x])
            if cnt[v] == m:
                k = _key(y, x)
                if bk is None or k < bk:
                    bk = k
                    best = v
    return best


def _components(mask):
    h, w = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
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
                out.append((min(_key(cy, cx) for cy, cx in cells), cells))
    out.sort(key=lambda t: t[0])
    return [c for _, c in out]


def _objs(P, T):
    mask = P != T
    res = []
    for cells in _components(mask):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        sub = np.full((y1 - y0 + 1, x1 - x0 + 1), -1, dtype=int)
        for y, x in cells:
            sub[y - y0, x - x0] = int(P[y, x])
        cs = frozenset(int(P[y, x]) for y, x in cells)
        res.append((cs, y0, x0, y1, x1, sub))
    return res


def _extend(a, b, rev):
    d = b.shape[0] - a.shape[0]
    if d <= 0:
        return b
    la = a.shape[0]
    order = range(la, -1, -1) if rev else range(la + 1)
    for i in order:
        if np.array_equal(b[:i], a[:i]) and np.array_equal(b[i + d:], a[i:]):
            return np.vstack([b[:i], b[i:i + d], b[i:]])
    return b


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = _background(g)
    found = None
    for va, s in STRIPS:
        L = g.shape[va]
        for p in range(2, L // 3 + 1):
            if L % p:
                continue
            n = L // p
            if va == 0:
                pans = [g[k * p:(k + 1) * p, :] for k in range(n)]
            else:
                pans = [g[:, k * p:(k + 1) * p] for k in range(n)]
            if s < 0:
                pans = pans[::-1]
            T = pans[-1]
            fm = T != bg
            if all(np.array_equal(P[fm], T[fm]) for P in pans):
                found = pans
                break
        if found is not None:
            break
    if found is None:
        return g.tolist()
    pans = found
    n = len(pans)
    T = pans[-1]
    out = T.copy()

    def colset(P):
        return frozenset(np.unique(P[P != T]).tolist())

    q = 1
    for cand in range(1, n - 1):
        ok = all(colset(pans[k]) == colset(pans[k - cand]) for k in range(cand, n - 1))
        if ok and n - 1 - 2 * cand >= 0:
            q = cand
            break
    A = pans[n - 1 - 2 * q]
    B = pans[n - 1 - q]
    oa = _objs(A, T)
    ob = _objs(B, T)
    used = set()
    H, W = out.shape
    for cs, by0, bx0, by1, bx1, bsub in ob:
        match = None
        for j, item in enumerate(oa):
            if j not in used and item[0] == cs:
                match = j
                break
        if match is None:
            continue
        used.add(match)
        _, ay0, ax0, ay1, ax1, asub = oa[match]
        c = bsub
        if asub.shape[1] != bsub.shape[1] and asub.shape[0] == bsub.shape[0]:
            c = _extend(asub.T, bsub.T, SX < 0).T
        elif asub.shape[0] != bsub.shape[0] and asub.shape[1] == bsub.shape[1]:
            c = _extend(asub, bsub, SY < 0)
        ch, cw = c.shape
        if SY > 0:
            cy = 2 * by0 - ay0
        else:
            cy = (2 * by1 - ay1) - (ch - 1)
        if SX > 0:
            cx = 2 * bx0 - ax0
        else:
            cx = (2 * bx1 - ax1) - (cw - 1)
        for y in range(ch):
            for x in range(cw):
                v = int(c[y, x])
                if v >= 0 and 0 <= cy + y < H and 0 <= cx + x < W:
                    out[cy + y, cx + x] = v
    return out.tolist()
'''


def build_program(d4, palette):
    dn = (1, 0)
    rt = (0, 1)
    if d4 >= 4:
        rt = (0, -1)
    for _ in range(d4 % 4):
        dn = (dn[1], -dn[0])
        rt = (rt[1], -rt[0])

    def strip(v):
        va = 0 if v[0] != 0 else 1
        return (va, v[va])

    strips = [strip(dn), strip(rt)]
    sy = dn[0] + rt[0]
    sx = dn[1] + rt[1]
    src = TEMPLATE
    src = src.replace('@DN@', repr(dn))
    src = src.replace('@RT@', repr(rt))
    src = src.replace('@STRIPS@', repr(strips))
    src = src.replace('@SY@', repr(sy))
    src = src.replace('@SX@', repr(sx))
    return src

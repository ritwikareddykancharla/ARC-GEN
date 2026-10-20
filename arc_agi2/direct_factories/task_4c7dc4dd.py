TEMPLATE = '''import numpy as np

ZERO = __ZERO__


def _runs(g):
    H, W = g.shape
    R = np.zeros((H, W), dtype=int)
    D = np.zeros((H, W), dtype=int)
    for y in range(H):
        for x in range(W - 1, -1, -1):
            R[y, x] = 1 + (R[y, x + 1] if x + 1 < W and g[y, x + 1] == g[y, x] else 0)
    for x in range(W):
        for y in range(H - 1, -1, -1):
            D[y, x] = 1 + (D[y + 1, x] if y + 1 < H and g[y + 1, x] == g[y, x] else 0)
    return R, D


def _parity(X):
    h, w = X.shape
    cols = {}
    for y in range(h):
        for x in range(w):
            if X[y, x] != ZERO:
                cols.setdefault((y + x) % 2, int(X[y, x]))
    if not cols:
        return None
    for p in (0, 1):
        if p not in cols:
            cols[p] = cols[1 - p]
    out = np.full(X.shape, ZERO, dtype=int)
    for y in range(h):
        for x in range(w):
            if X[y, x] == ZERO:
                out[y, x] = cols[(y + x) % 2]
    return out


def _mirror(X, fc):
    nz = np.argwhere(X != ZERO)
    if len(nz) == 0:
        return None
    h, w = X.shape
    out = X.copy()
    for F in (X[:, ::-1], X[::-1, :], X[::-1, ::-1]):
        out = np.where(out == ZERO, F, out)
    y0, x0 = nz.min(0)
    y1, x1 = nz.max(0)
    cov = np.zeros(X.shape, dtype=bool)
    boxes = [(y0, x0, y1, x1), (y0, w - 1 - x1, y1, w - 1 - x0),
             (h - 1 - y1, x0, h - 1 - y0, x1),
             (h - 1 - y1, w - 1 - x1, h - 1 - y0, w - 1 - x0)]
    for a, b, c, d in boxes:
        cov[a:c + 1, b:d + 1] = True
    out[(~cov) & (out == ZERO)] = fc
    return out


def _lines(X, c):
    out = X.copy()
    h, w = X.shape
    for y in range(h):
        xs = list(np.nonzero(X[y] != ZERO)[0])
        for a, b in zip(xs, xs[1:]):
            out[y, a + 1:b] = c
    for x in range(w):
        ys = list(np.nonzero(X[:, x] != ZERO)[0])
        for a, b in zip(ys, ys[1:]):
            out[a + 1:b, x] = c
    return out


def _transform(grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    R, D = _runs(g)

    def bordered(y0, x0, y1, x1):
        if y1 >= H or x1 >= W:
            return False
        c = g[y0, x0]
        w = x1 - x0 + 1
        h = y1 - y0 + 1
        return (R[y0, x0] >= w and D[y0, x0] >= h and g[y1, x0] == c and
                R[y1, x0] >= w and g[y0, x1] == c and D[y0, x1] >= h)

    groups = {}
    for y0 in range(H):
        for x0 in range(W):
            r = int(R[y0, x0])
            d = int(D[y0, x0])
            if r < 4 or d < 4:
                continue
            for hh in range(4, min(15, d) + 1):
                for ww in range(4, min(15, r) + 1):
                    y1 = y0 + hh - 1
                    x1 = x0 + ww - 1
                    if bordered(y0, x0, y1, x1):
                        groups.setdefault((hh, ww), []).append((y0, x0, y1, x1))
    keys = [k for k, v in groups.items() if len(v) == 4]
    if not keys:
        return [[int(v) for v in row] for row in grid]
    key = max(keys, key=lambda k: (k[0] * k[1], -abs(k[0] - k[1])))
    frames = groups[key]
    inter = [g[a + 1:c, b + 1:d].copy() for a, b, c, d in frames]
    fcol = [int(g[a, b]) for a, b, c, d in frames]
    empties = [i for i in range(4) if not (inter[i] != ZERO).any()]
    if not empties:
        return inter[0].tolist()
    ei = empties[0]
    fy0, fx0, fy1, fx1 = frames[ei]
    best = None
    for y0 in range(fy0):
        for y1 in range(fy1 + 1, H):
            for x0 in range(fx0):
                for x1 in range(fx1 + 1, W):
                    area = (y1 - y0) * (x1 - x0)
                    if best is not None and area >= best[0]:
                        continue
                    if not bordered(y0, x0, y1, x1):
                        continue
                    inside = [i for i, (a, b, c, d) in enumerate(frames)
                              if a > y0 and b > x0 and c < y1 and d < x1]
                    if len(inside) == 2 and ei in inside:
                        best = (area, [i for i in inside if i != ei][0])
    if best is not None:
        qi = best[1]
    else:
        qi = min([i for i in range(4) if i != ei],
                 key=lambda i: (frames[i][0] - fy0) ** 2 + (frames[i][1] - fx0) ** 2)
    ex = [i for i in range(4) if i not in (ei, qi)]
    Q = inter[qi]
    pairs = [(ex[0], ex[1]), (ex[1], ex[0])]
    result = None
    for s, t in pairs:
        r = _parity(inter[s])
        if r is not None and np.array_equal(r, inter[t]):
            result = _parity(Q)
            break
    if result is None:
        for s, t in pairs:
            r = _mirror(inter[s], fcol[s])
            if r is not None and np.array_equal(r, inter[t]):
                result = _mirror(Q, fcol[qi])
                break
    if result is None:
        for s, t in pairs:
            S = inter[s]
            cands = sorted(set(np.unique(inter[t]).tolist()) - {ZERO})
            for c in cands:
                if np.array_equal(_lines(S, c), inter[t]):
                    diff = set(np.unique(Q).tolist()) - {ZERO} - set(np.unique(S).tolist())
                    cq = diff.pop() if len(diff) == 1 else c
                    result = _lines(Q, cq)
                    break
            if result is not None:
                break
    if result is None:
        result = Q.copy()
    return [[int(v) for v in row] for row in result]


def solve(demonstrations, grid):
    return _transform(grid)
'''


def build_program(d4, palette):
    zero = int(palette[0])
    return TEMPLATE.replace('__ZERO__', str(zero))

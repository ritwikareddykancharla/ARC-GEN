TEMPLATE = '''import numpy as np

AXIS = __AXIS__


def _divider_split(g, m, nr, nc):
    lines = set()
    for j in range(nr - 1):
        row = g[(m + 1) * j + m, :]
        if not (row == row[0]).all():
            return None
        lines.add(int(row[0]))
    for j in range(nc - 1):
        col = g[:, (m + 1) * j + m]
        if not (col == col[0]).all():
            return None
        lines.add(int(col[0]))
    if len(lines) != 1:
        return None
    small = np.zeros((nr, nc), dtype=int)
    for i in range(nr):
        for j in range(nc):
            blk = g[i * (m + 1):i * (m + 1) + m, j * (m + 1):j * (m + 1) + m]
            if blk.size == 0 or not (blk == blk[0, 0]).all():
                return None
            small[i, j] = int(blk[0, 0])
    return small


def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b - a > 1:
            out.append(a + 1)
    return out


def _fallback(g):
    H, W = g.shape
    urows = {r: int(g[r, 0]) for r in range(H) if (g[r] == g[r, 0]).all()}
    ucols = {c: int(g[0, c]) for c in range(W) if (g[:, c] == g[0, c]).all()}
    common = sorted(set(urows.values()) & set(ucols.values()))
    if not common:
        return np.array([[int(g[0, 0])]])
    def score(k):
        return sum(v == k for v in urows.values()) + sum(v == k for v in ucols.values())
    lc = max(common, key=score)
    rc = [r for r, v in urows.items() if v == lc]
    cc = [c for c, v in ucols.items() if v == lc]
    ys = _spans(rc, H)
    xs = _spans(cc, W)
    if not ys or not xs:
        return np.array([[int(g[0, 0])]])
    small = np.zeros((len(ys), len(xs)), dtype=int)
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            small[i, j] = int(g[y, x])
    return small


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    H, W = g.shape
    best = None
    for m in range(1, max(H, W) + 1):
        if (H + 1) % (m + 1) or (W + 1) % (m + 1):
            continue
        nr = (H + 1) // (m + 1)
        nc = (W + 1) // (m + 1)
        if nr < 1 or nc < 1:
            continue
        small = _divider_split(g, m, nr, nc)
        if small is None:
            continue
        key = (int(nr == nc and 3 <= nr <= 4 and 2 <= m <= 5), m)
        if best is None or key > best[0]:
            best = (key, small)
    small = best[1] if best is not None else _fallback(g)
    if AXIS == 'lr':
        out = small[:, ::-1]
    else:
        out = small[::-1, :]
    return out.copy().tolist()
'''


def build_program(d4, palette):
    axis = 'lr' if (d4 % 4) in (0, 2) else 'ud'
    return TEMPLATE.replace('__AXIS__', repr(axis))

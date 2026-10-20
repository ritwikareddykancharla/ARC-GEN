def build_program(d4, palette):
    bg = int(palette[8])
    line = int(palette[1])
    template = '''import numpy as np

BG = __BG__
LINE = __LINE__


def _mirror_fn(g):
    ys, xs = np.nonzero(g == LINE)
    if len(ys) < 2:
        return None
    ys = [int(v) for v in ys]
    xs = [int(v) for v in xs]
    if len(set(xs)) == 1:
        c = xs[0]
        return lambda y, x: (y, 2 * c - x)
    if len(set(ys)) == 1:
        r = ys[0]
        return lambda y, x: (2 * r - y, x)
    diffs = set(y - x for y, x in zip(ys, xs))
    if len(diffs) == 1:
        k = diffs.pop()
        return lambda y, x: (x + k, y - k)
    sums = set(y + x for y, x in zip(ys, xs))
    if len(sums) == 1:
        s = sums.pop()
        return lambda y, x: (s - x, s - y)
    return None


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    f = _mirror_fn(g)
    if f is None:
        return out.tolist()
    counts = {}
    for v in np.unique(g):
        v = int(v)
        if v == BG or v == LINE:
            continue
        counts[v] = int((g == v).sum())
    if not counts:
        return out.tolist()
    rare = min(counts, key=lambda v: (counts[v], v))
    ys, xs = np.nonzero(g == rare)
    for y, x in zip(ys.tolist(), xs.tolist()):
        ny, nx = f(y, x)
        if 0 <= ny < H and 0 <= nx < W and out[ny, nx] == BG:
            out[ny, nx] = rare
    return [[int(v) for v in row] for row in out.tolist()]
'''
    return template.replace('__BG__', str(bg)).replace('__LINE__', str(line))

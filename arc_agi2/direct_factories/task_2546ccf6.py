def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = __BG__


def _dividers(g, bg):
    H, W = g.shape
    rows = [y for y in range(H) if g[y, 0] != bg and bool((g[y] == g[y, 0]).all())]
    cols = [x for x in range(W) if g[0, x] != bg and bool((g[:, x] == g[0, x]).all())]
    return rows, cols


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
    H, W = g.shape
    bg = BG
    if not bool((g == bg).any()):
        vals, cnt = np.unique(g, return_counts=True)
        bg = int(vals[int(np.argmax(cnt))])
    rows, cols = _dividers(g, bg)
    ys = _spans(rows, H)
    xs = _spans(cols, W)

    def panel(i, j):
        return g[ys[i][0]:ys[i][1] + 1, xs[j][0]:xs[j][1] + 1]

    cont = {}
    for i in range(len(ys)):
        for j in range(len(xs)):
            cont[(i, j)] = set(int(v) for v in np.unique(panel(i, j)).tolist()) - {bg}

    for i in range(len(ys) - 1):
        for j in range(len(xs) - 1):
            blk = [(i, j), (i, j + 1), (i + 1, j), (i + 1, j + 1)]
            cs = [cont[k] for k in blk]
            empty = [k for k, c in zip(blk, cs) if not c]
            full = [c for c in cs if c]
            if len(empty) != 1 or len(full) != 3:
                continue
            if not all(len(c) == 1 and c == full[0] for c in full):
                continue
            ei, ej = empty[0]
            hj = j + 1 if ej == j else j
            vi = i + 1 if ei == i else i
            y0, y1 = ys[ei]
            x0, x1 = xs[ej]
            shape = (y1 - y0 + 1, x1 - x0 + 1)
            hsrc = panel(ei, hj)[:, ::-1]
            vsrc = panel(vi, ej)[::-1, :]
            if hsrc.shape == shape:
                out[y0:y1 + 1, x0:x1 + 1] = hsrc
            elif vsrc.shape == shape:
                out[y0:y1 + 1, x0:x1 + 1] = vsrc
    return out.tolist()
'''
    return src.replace('__BG__', str(bg))

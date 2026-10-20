def build_program(d4, palette):
    pal = [int(palette[i]) for i in range(10)]
    src = '''import numpy as np

GREY = @GREY@
BG = @BG@
CA = @CA@
CB = @CB@


def _segments(n, cuts):
    cutset = set(cuts)
    out = []
    start = 0
    for k in range(n + 1):
        if k == n or k in cutset:
            if k > start:
                out.append((start, k))
            start = k + 1
    return out


def _dominant(p):
    vals, counts = np.unique(p, return_counts=True)
    best = None
    bestn = -1
    for v, n in zip(vals.tolist(), counts.tolist()):
        if v == BG or v == GREY:
            continue
        if n > bestn:
            best = v
            bestn = n
    if best is None:
        return BG
    return int(best)


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    h, w = g.shape
    gcols = [x for x in range(w) if np.all(g[:, x] == GREY)]
    grows = [y for y in range(h) if np.all(g[y, :] == GREY)]
    if len(gcols) >= len(grows):
        s = h - 2
        pans = [g[:, a:b] for a, b in _segments(w, gcols)]
    else:
        s = w - 2
        pans = [g[a:b, :] for a, b in _segments(h, grows)]
    n = len(pans)
    ia = max(range(n), key=lambda k: int(np.sum(pans[k] == CA)))
    ib = max(range(n), key=lambda k: int(np.sum(pans[k] == CB)))
    rest = [k for k in range(n) if k != ia and k != ib]
    rest.sort(key=lambda k: abs(k - ib))
    am = pans[ia][1:1 + s, 1:1 + s] == CA
    bm = pans[ib][1:1 + s, 1:1 + s] == CB
    fg = _dominant(pans[rest[0]])
    bgc = _dominant(pans[rest[1]]) if len(rest) > 1 else BG
    out = np.full((s * s, s * s), bgc, dtype=int)
    tile = np.where(am, fg, bgc)
    for i in range(s):
        for j in range(s):
            if bm[i, j]:
                out[i * s:(i + 1) * s, j * s:(j + 1) * s] = tile
    return out.tolist()
'''
    src = src.replace('@GREY@', str(pal[5]))
    src = src.replace('@BG@', str(pal[0]))
    src = src.replace('@CA@', str(pal[1]))
    src = src.replace('@CB@', str(pal[2]))
    return src

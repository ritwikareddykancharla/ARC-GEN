def build_program(d4, palette):
    bg = int(palette[0])
    div = int(palette[8])
    cross = int(palette[6])
    src = '''import numpy as np

BG = __BG__
DIV = __DIV__
CROSS = __CROSS__


def _bands(flags):
    res = []
    start = None
    for i, f in enumerate(flags):
        if f:
            if start is not None:
                res.append((start, i - 1))
                start = None
        elif start is None:
            start = i
    if start is not None:
        res.append((start, len(flags) - 1))
    return res


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    rb = _bands([bool(np.all(g[y, :] == DIV)) for y in range(H)])
    cb = _bands([bool(np.all(g[:, x] == DIV)) for x in range(W)])
    rid = [-1] * H
    for i, (a, b) in enumerate(rb):
        for y in range(a, b + 1):
            rid[y] = i
    cid = [-1] * W
    for i, (a, b) in enumerate(cb):
        for x in range(a, b + 1):
            cid[x] = i
    markers = {}
    for y in range(H):
        for x in range(W):
            c = int(g[y, x])
            if c == BG or c == DIV or rid[y] < 0 or cid[x] < 0:
                continue
            markers.setdefault(c, set()).add((rid[y], cid[x]))
    cover = {}
    for c in sorted(markers):
        cells = sorted(markers[c])
        for cell in cells:
            cover.setdefault(cell, set()).add(c)
        for i in range(len(cells)):
            r1, c1 = cells[i]
            for j in range(i + 1, len(cells)):
                r2, c2 = cells[j]
                if r1 == r2:
                    span = [(r1, k) for k in range(min(c1, c2), max(c1, c2) + 1)]
                elif c1 == c2:
                    span = [(k, c1) for k in range(min(r1, r2), max(r1, r2) + 1)]
                else:
                    span = []
                for cell in span:
                    cover.setdefault(cell, set()).add(c)
    out = g.copy()
    for (r, k), cs in cover.items():
        y0, y1 = rb[r]
        x0, x1 = cb[k]
        out[y0:y1 + 1, x0:x1 + 1] = CROSS if len(cs) > 1 else next(iter(cs))
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__DIV__', str(div)).replace('__CROSS__', str(cross))

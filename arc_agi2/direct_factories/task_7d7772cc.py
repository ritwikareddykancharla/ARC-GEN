def build_program(d4, palette):
    pal = [int(p) for p in palette]
    header = '# 7d7772cc visible-coordinate solver. d4=%d palette=%s\n' % (int(d4), pal)
    header += '# Native generator already randomises flip/transpose, so every visible wall\n'
    header += '# orientation is in-domain. Wall axis and inside side are read from pixels.\n'
    header += '# Colour roles (wall, backgrounds, markers) are inferred, not hard-coded.\n'
    body = '''import numpy as np
from collections import Counter


def _expected(shape, kind, i, d):
    H, W = shape
    e = np.zeros((H, W), dtype=bool)
    if kind == 'row':
        e[i, :] = True
        if d == 1:
            e[i + 1:, 0] = True
            e[i + 1:, W - 1] = True
        else:
            e[:i, 0] = True
            e[:i, W - 1] = True
    else:
        e[:, i] = True
        if d == 1:
            e[0, i + 1:] = True
            e[H - 1, i + 1:] = True
        else:
            e[0, :i] = True
            e[H - 1, :i] = True
    return e


def _find_wall(g):
    H, W = g.shape
    best = None
    for y in range(H):
        c = int(g[y, 0])
        if not (g[y, :] == c).all():
            continue
        for d in (1, -1):
            if not (0 <= y + d < H and 0 <= y - d < H):
                continue
            e = _expected(g.shape, 'row', y, d)
            s = int(((g == c) != e).sum())
            if best is None or s < best[0]:
                best = (s, 'row', y, d, c)
    for x in range(W):
        c = int(g[0, x])
        if not (g[:, x] == c).all():
            continue
        for d in (1, -1):
            if not (0 <= x + d < W and 0 <= x - d < W):
                continue
            e = _expected(g.shape, 'col', x, d)
            s = int(((g == c) != e).sum())
            if best is None or s < best[0]:
                best = (s, 'col', x, d, c)
    return best


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    w = _find_wall(g)
    if w is None:
        return g.tolist()
    _, kind, i, d, c = w
    res = g.copy()
    if kind == 'row':
        lines = list(range(0, i)) if d == 1 else list(range(i + 1, H))
        region = g[lines, :]
        obg = Counter(region.ravel().tolist()).most_common(1)[0][0]
        ref = g[i + d, :]
        near = i - d
        far = 0 if d == 1 else H - 1
        markers = [(y, x) for y in lines for x in range(W) if g[y, x] != obg]
        for y, x in markers:
            res[y, x] = obg
        for y, x in markers:
            v = int(g[y, x])
            ty = near if v == int(ref[x]) else far
            res[ty, x] = v
    else:
        lines = list(range(0, i)) if d == 1 else list(range(i + 1, W))
        region = g[:, lines]
        obg = Counter(region.ravel().tolist()).most_common(1)[0][0]
        ref = g[:, i + d]
        near = i - d
        far = 0 if d == 1 else W - 1
        markers = [(y, x) for x in lines for y in range(H) if g[y, x] != obg]
        for y, x in markers:
            res[y, x] = obg
        for y, x in markers:
            v = int(g[y, x])
            tx = near if v == int(ref[y]) else far
            res[y, tx] = v
    return res.tolist()
'''
    return header + body

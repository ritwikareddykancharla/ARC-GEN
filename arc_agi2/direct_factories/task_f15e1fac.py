TEMPLATE = '''import numpy as np

SEED = __SEED__
MARK = __MARK__
BG = __BG__

_DIR = {'top': (1, 0), 'bottom': (-1, 0), 'left': (0, 1), 'right': (0, -1)}


def _edges(cells, H, W):
    res = []
    if not cells:
        return res
    ys = set(c[0] for c in cells)
    xs = set(c[1] for c in cells)
    if ys == {0}:
        res.append('top')
    if ys == {H - 1}:
        res.append('bottom')
    if xs == {0}:
        res.append('left')
    if xs == {W - 1}:
        res.append('right')
    return res


def _horiz(e):
    return e in ('top', 'bottom')


def _spread(cells, e):
    idx = 1 if _horiz(e) else 0
    return len(set(c[idx] for c in cells))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    seeds = [(int(p[0]), int(p[1])) for p in np.argwhere(g == SEED)]
    marks = [(int(p[0]), int(p[1])) for p in np.argwhere(g == MARK)]
    if not seeds:
        return out.tolist()
    e8s = _edges(seeds, H, W)
    e2s = _edges(marks, H, W)
    best = None
    for e8 in e8s:
        for e2 in e2s:
            if _horiz(e8) != _horiz(e2):
                key = (_spread(seeds, e8), _spread(marks, e2))
                if best is None or key > best[0]:
                    best = (key, e8, e2)
    if best is None:
        if not e8s:
            return out.tolist()
        e8 = max(e8s, key=lambda e: _spread(seeds, e))
        e2 = None
    else:
        e8 = best[1]
        e2 = best[2]
    dy, dx = _DIR[e8]
    a = 0 if _horiz(e8) else 1
    if e8 == 'top' or e8 == 'left':
        base = 0
    elif e8 == 'bottom':
        base = H - 1
    else:
        base = W - 1
    limit = H if a == 0 else W
    if e2 is None:
        sy, sx = 0, 0
        dists = []
    else:
        sy, sx = _DIR[e2]
        dists = sorted(abs(m[a] - base) for m in marks)
    for (y0, x0) in seeds:
        for k in range(limit):
            inc = sum(1 for dd in dists if 0 < dd <= k)
            y = y0 + k * dy + inc * sy
            x = x0 + k * dx + inc * sx
            if 0 <= y < H and 0 <= x < W and out[y, x] != MARK:
                out[y, x] = SEED
    return out.tolist()
'''


def build_program(d4, palette):
    pal = list(palette)
    seed = int(pal[8])
    mark = int(pal[2])
    bg = int(pal[0])
    src = TEMPLATE.replace('__SEED__', str(seed))
    src = src.replace('__MARK__', str(mark))
    src = src.replace('__BG__', str(bg))
    return src

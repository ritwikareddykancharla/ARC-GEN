TEMPLATE = '''import numpy as np
from collections import Counter, deque

MARK = __MARK__
ANTI = __ANTI__
ROWS_FIRST = __ROWS__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _shape(cells):
    y0 = min(c[0] for c in cells)
    x0 = min(c[1] for c in cells)
    return tuple(sorted((y - y0, x - x0) for y, x in cells))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    m = g == MARK
    clean_rows = [y for y in range(H) if not m[y].any()]
    clean_cols = [x for x in range(W) if not m[:, x].any()]

    def by_row(y, x):
        ok = ~m[y]
        for y2 in clean_rows:
            if (g[y2][ok] == g[y][ok]).all():
                return int(g[y2, x])
        return None

    def by_col(y, x):
        ok = ~m[:, x]
        for x2 in clean_cols:
            if (g[:, x2][ok] == g[:, x][ok]).all():
                return int(g[y, x2])
        return None

    order = (by_row, by_col) if ROWS_FIRST else (by_col, by_row)

    def underlying(y, x):
        if H == W:
            if ANTI:
                my, mx = W - 1 - x, H - 1 - y
            else:
                my, mx = x, y
            if g[my, mx] != MARK:
                return int(g[my, mx])
        for f in order:
            v = f(y, x)
            if v is not None:
                return v
        return None

    cache = {}

    def comps_of(c):
        if c not in cache:
            cache[c] = _components(g == c)
        return cache[c]

    for comp in _components(m):
        key = _shape(comp)
        vals = [underlying(y, x) for y, x in comp]
        vals = [v for v in vals if v is not None and v != MARK]
        if vals:
            cols = [Counter(vals).most_common(1)[0][0]]
        else:
            cols = [int(c) for c in np.unique(g) if c != MARK]
        for c in cols:
            for cc in comps_of(c):
                if _shape(cc) == key:
                    for y, x in cc:
                        out[y, x] = MARK
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    rot = d4 % 4
    flip = d4 >= 4
    anti = ((rot + (1 if flip else 0)) % 2) == 1
    rows_first = (rot % 2) == 0
    mark = int(palette[8]) if len(palette) > 8 else 8
    prog = TEMPLATE.replace('__MARK__', str(mark))
    prog = prog.replace('__ANTI__', str(anti))
    prog = prog.replace('__ROWS__', str(rows_first))
    return prog

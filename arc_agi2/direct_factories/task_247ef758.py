def build_program(d4, palette):
    sides = ['top', 'right', 'bottom', 'left']
    k = d4 % 4
    # Original layout: legend on the LEFT; the higher legend motif (toward TOP) wins overlaps.
    # A horizontal flip (d4>=4) moves the legend to the RIGHT and leaves TOP in place.
    # Each clockwise rotation maps top->right->bottom->left->top.
    if d4 >= 4:
        l0, p0 = 1, 0
    else:
        l0, p0 = 3, 0
    lside = sides[(l0 + k) % 4]
    pside = sides[(p0 + k) % 4]
    # The original floor-centre becomes a ceil-centre on any visible axis whose direction is reversed.
    if pside in ('top', 'bottom'):
        row_ceil = (pside == 'bottom')
        col_ceil = (lside == 'right')
    else:
        col_ceil = (pside == 'right')
        row_ceil = (lside == 'bottom')
    bg = int(palette[0])
    src = '''import numpy as np
from collections import Counter

BG = __BG__
LSIDE = __LSIDE__
PSIDE = __PSIDE__
ROW_CEIL = __ROWCEIL__
COL_CEIL = __COLCEIL__


def _uniform_line(v):
    return v[0] != BG and bool((v == v[0]).all())


def _find_divider(g):
    H, W = g.shape
    if LSIDE in ('left', 'right'):
        idx = range(W) if LSIDE == 'left' else range(W - 1, -1, -1)
        for x in idx:
            if _uniform_line(g[:, x]):
                return x
    else:
        idx = range(H) if LSIDE == 'top' else range(H - 1, -1, -1)
        for y in idx:
            if _uniform_line(g[y, :]):
                return y
    return None


def _centre(a, b, ceil):
    return (a + b + 1) // 2 if ceil else (a + b) // 2


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    d = _find_divider(g)
    if d is None:
        return g.tolist()
    if LSIDE == 'left':
        r0, r1, c0, c1 = 0, H - 1, d + 1, W - 1
        lr0, lr1, lc0, lc1 = 0, H - 1, 0, d - 1
    elif LSIDE == 'right':
        r0, r1, c0, c1 = 0, H - 1, 0, d - 1
        lr0, lr1, lc0, lc1 = 0, H - 1, d + 1, W - 1
    elif LSIDE == 'top':
        r0, r1, c0, c1 = d + 1, H - 1, 0, W - 1
        lr0, lr1, lc0, lc1 = 0, d - 1, 0, W - 1
    else:
        r0, r1, c0, c1 = 0, d - 1, 0, W - 1
        lr0, lr1, lc0, lc1 = d + 1, H - 1, 0, W - 1
    if r1 - r0 < 2 or c1 - c0 < 2:
        return g.tolist()
    border = (list(g[r0, c0:c1 + 1]) + list(g[r1, c0:c1 + 1]) +
              list(g[r0:r1 + 1, c0]) + list(g[r0:r1 + 1, c1]))
    border = [int(v) for v in border]
    fbg = Counter(border).most_common(1)[0][0]
    rows, cols = {}, {}
    # Markers on vertical borders mark their row.
    for y in range(r0 + 1, r1):
        for c in (int(g[y, c0]), int(g[y, c1])):
            if c != fbg:
                rows.setdefault(c, set()).add(y)
    # Markers on horizontal borders mark their column.
    for x in range(c0 + 1, c1):
        for c in (int(g[r0, x]), int(g[r1, x])):
            if c != fbg:
                cols.setdefault(c, set()).add(x)
    motifs = {}
    for y in range(max(lr0, 0), lr1 + 1):
        for x in range(max(lc0, 0), lc1 + 1):
            c = int(g[y, x])
            if c != BG:
                motifs.setdefault(c, []).append((y, x))
    order = []
    for c, cells in motifs.items():
        ys = [p[0] for p in cells]
        xs = [p[1] for p in cells]
        if PSIDE == 'top':
            key = min(ys)
        elif PSIDE == 'bottom':
            key = (H - 1) - max(ys)
        elif PSIDE == 'left':
            key = min(xs)
        else:
            key = (W - 1) - max(xs)
        order.append((key, c, cells))
    # Paint the motif farthest from the priority side first; the nearest one ends on top.
    order.sort(key=lambda t: (t[0], t[1]), reverse=True)
    for _, c, cells in order:
        if c not in rows or c not in cols:
            continue
        ys = [p[0] for p in cells]
        xs = [p[1] for p in cells]
        cy = _centre(min(ys), max(ys), ROW_CEIL)
        cx = _centre(min(xs), max(xs), COL_CEIL)
        for rr in sorted(rows[c]):
            for cc in sorted(cols[c]):
                for y, x in cells:
                    yy, xx = rr + y - cy, cc + x - cx
                    if 0 <= yy < H and 0 <= xx < W:
                        g[yy, xx] = c
        for y, x in cells:
            g[y, x] = BG
    return g.tolist()
'''
    src = src.replace('__BG__', repr(bg))
    src = src.replace('__LSIDE__', repr(lside))
    src = src.replace('__PSIDE__', repr(pside))
    src = src.replace('__ROWCEIL__', repr(bool(row_ceil)))
    src = src.replace('__COLCEIL__', repr(bool(col_ceil)))
    return src

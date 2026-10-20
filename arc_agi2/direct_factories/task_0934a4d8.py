_TEMPLATE = """import numpy as np
from collections import Counter

MASK = __MASK__
AY_OFF = __AYOFF__
AX_OFF = __AXOFF__
R = 6


def _mirror_score(g, known, a, rows):
    if not rows:
        g = g.T
        known = known.T
    n = g.shape[0]
    agree = 0
    disagree = 0
    for i in range(n):
        j = a - i
        if j <= i or j >= n:
            continue
        both = known[i] & known[j]
        eq = g[i] == g[j]
        agree += int(np.sum(both & eq))
        disagree += int(np.sum(both & ~eq))
    return (disagree == 0 and agree > 0, agree - 50 * disagree)


def _axis(g, known, a, rows):
    if _mirror_score(g, known, a, rows)[0]:
        return a
    n = g.shape[0] if rows else g.shape[1]
    best = None
    for b in range(1, 2 * n - 1):
        s = _mirror_score(g, known, b, rows)
        if best is None or s > best[0]:
            best = (s, b)
    return best[1] if best is not None else a


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    mask = g == MASK
    if not mask.any():
        return [[int(v) for v in row] for row in g]
    ys, xs = np.where(mask)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    known = ~mask
    val = g.copy()
    ay = _axis(g, known, H + AY_OFF, True)
    ax = _axis(g, known, W + AX_OFF, False)

    def inside(py, px):
        return 0 <= py < H and 0 <= px < W

    changed = True
    while changed:
        changed = False
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if known[y, x]:
                    continue
                for py, px in ((y, ax - x), (ay - y, x), (ay - y, ax - x)):
                    if inside(py, px) and known[py, px]:
                        val[y, x] = val[py, px]
                        known[y, x] = True
                        changed = True
                        break

    maps = []
    for k in range(-(W - 1), H):
        maps.append((0, k))
    for c in range(0, H + W - 1):
        maps.append((1, c))

    def apply(m, y, x):
        if m[0] == 0:
            return x + m[1], y - m[1]
        return m[1] - x, m[1] - y

    def window_stats(y, x, m):
        agree = 0
        for yy in range(max(0, y - R), min(H, y + R + 1)):
            for xx in range(max(0, x - R), min(W, x + R + 1)):
                if not known[yy, xx]:
                    continue
                py, px = apply(m, yy, xx)
                if inside(py, px) and known[py, px]:
                    if val[yy, xx] == val[py, px]:
                        agree += 1
                    else:
                        return agree, 1
        return agree, 0

    changed = True
    while changed:
        changed = False
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if known[y, x]:
                    continue
                best = None
                for m in maps:
                    py, px = apply(m, y, x)
                    if not (inside(py, px) and known[py, px]):
                        continue
                    agree, disagree = window_stats(y, x, m)
                    if disagree == 0 and agree >= 10:
                        if best is None or agree > best[0]:
                            best = (agree, py, px)
                if best is not None:
                    val[y, x] = val[best[1], best[2]]
                    known[y, x] = True
                    changed = True

    if not known[y0:y1 + 1, x0:x1 + 1].all():
        bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if not known[y, x]:
                    val[y, x] = bg
                    known[y, x] = True
    out = val[y0:y1 + 1, x0:x1 + 1]
    return [[int(v) for v in row] for row in out]
"""


def build_program(d4, palette):
    d4 = int(d4) % 8
    mask = int(palette[8])
    row_flip = False
    col_flip = d4 >= 4
    for _ in range(d4 % 4):
        row_flip, col_flip = col_flip, (not row_flip)
    ay_off = -3 if row_flip else 1
    ax_off = -3 if col_flip else 1
    src = _TEMPLATE
    src = src.replace('__MASK__', str(mask))
    src = src.replace('__AYOFF__', str(ay_off))
    src = src.replace('__AXOFF__', str(ax_off))
    return src

def build_program(d4, palette):
    bar_colour = int(palette[4])
    green_colour = int(palette[3])
    template = '''import numpy as np
from collections import Counter

BAR = __BAR__
GREEN = __GREEN__


def _background(g):
    cnt = Counter(g.ravel().tolist())
    cnt.pop(BAR, None)
    cnt.pop(GREEN, None)
    if not cnt:
        return int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    return int(cnt.most_common(1)[0][0])


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.where(g == BAR)
    if ys.size == 0:
        return out.tolist()
    bg = _background(g)
    rows = sorted(set(ys.tolist()))
    cols = sorted(set(xs.tolist()))
    if len(rows) == 1 and len(cols) > 1:
        horizontal = True
    elif len(cols) == 1 and len(rows) > 1:
        horizontal = False
    else:
        r0, c0 = rows[0], cols[0]
        horizontal = r0 in (0, H - 1) and not (c0 in (0, W - 1))
        if not horizontal and not (c0 in (0, W - 1)):
            horizontal = True
    if horizontal:
        n = H
        start = rows[0] if rows[0] in (0, H - 1) else (0 if rows[0] < H - 1 - rows[0] else H - 1)
        step = 1 if start == 0 else -1
        lo, hi = int(xs.min()), int(xs.max())
    else:
        n = W
        start = cols[0] if cols[0] in (0, W - 1) else (0 if cols[0] < W - 1 - cols[0] else W - 1)
        step = 1 if start == 0 else -1
        lo, hi = int(ys.min()), int(ys.max())
    for d in range(n):
        idx = start + d * step
        if not (0 <= idx < n):
            break
        m = d % 6
        if horizontal:
            if m % 2 == 1:
                out[idx, lo:hi + 1] = bg
            elif m == 4:
                out[idx, g[idx, :] != bg] = GREEN
                out[idx, lo:hi + 1] = GREEN
            else:
                out[idx, lo:hi + 1] = BAR
        else:
            if m % 2 == 1:
                out[lo:hi + 1, idx] = bg
            elif m == 4:
                out[g[:, idx] != bg, idx] = GREEN
                out[lo:hi + 1, idx] = GREEN
            else:
                out[lo:hi + 1, idx] = BAR
    return out.tolist()
'''
    return template.replace('__BAR__', repr(bar_colour)).replace('__GREEN__', repr(green_colour))

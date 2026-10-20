_TEMPLATE = '''import numpy as np

# Anchor side of the frieze in visible coordinates; extension runs away from it.
SIDE = __SIDE__
# Background colour (original colour 0 under the episode palette).
BG = __BG__


def _count(g):
    h, w = g.shape
    return w if SIDE in ('left', 'right') else h


def _line(g, t):
    h, w = g.shape
    if SIDE == 'left':
        return g[:, t]
    if SIDE == 'right':
        return g[:, w - 1 - t]
    if SIDE == 'top':
        return g[t, :]
    return g[h - 1 - t, :]


def _put(g, t, v):
    h, w = g.shape
    if SIDE == 'left':
        g[:, t] = v
    elif SIDE == 'right':
        g[:, w - 1 - t] = v
    elif SIDE == 'top':
        g[t, :] = v
    else:
        g[h - 1 - t, :] = v


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if g.ndim != 2 or g.size == 0:
        return [list(r) for r in grid]
    n = _count(g)
    lines = [_line(g, t).copy() for t in range(n)]
    filled = [t for t in range(n) if (lines[t] != BG).any()]
    if not filled:
        return g.tolist()
    length = max(filled) + 1
    period = length
    for cand in range(1, length):
        ok = True
        for t in range(cand, length):
            if not np.array_equal(lines[t], lines[t - cand]):
                ok = False
                break
        if ok:
            period = cand
            break
    out = g.copy()
    for t in range(length, n):
        src = _line(out, t - period).copy()
        _put(out, t, src)
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4)
    sides = ['left', 'top', 'right', 'bottom']
    start = 2 if d4 >= 4 else 0
    side = sides[(start + d4 % 4) % 4]
    bg = int(palette[0])
    return _TEMPLATE.replace('__SIDE__', repr(side)).replace('__BG__', repr(bg))

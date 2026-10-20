def build_program(d4, palette):
    d4 = int(d4)
    k = d4 % 4
    flip = d4 >= 4
    hole = int(palette[0])
    # Original slot lines are columns; odd rotation counts turn them into rows.
    slots_are_columns = (k % 2 == 0)
    # Original order runs left to right, and the most-holed slot goes leftmost.
    # Under rotation, original column c becomes:
    #   k=0: column c
    #   k=1: row c
    #   k=2: column W-1-c
    #   k=3: row W-1-c
    # A horizontal flip, applied first, reverses this order once more.
    reverse = (k in (2, 3)) != flip
    src = '''import numpy as np

HOLE = %d
SLOTS_ARE_COLUMNS = %r
REVERSE = %r


def _line(g, i):
    if SLOTS_ARE_COLUMNS:
        return g[:, i].copy()
    return g[i, :].copy()


def _put(g, i, v):
    if SLOTS_ARE_COLUMNS:
        g[:, i] = v
    else:
        g[i, :] = v


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    vals, cnts = np.unique(g, return_counts=True)
    others = [(int(c), int(v)) for v, c in zip(vals, cnts) if int(v) != HOLE]
    if not others:
        return g.tolist()
    others.sort(key=lambda t: (-t[0], t[1]))
    bg = others[0][1]
    n = W if SLOTS_ARE_COLUMNS else H
    slots = []
    for i in range(n):
        ln = _line(g, i)
        if np.all(ln == HOLE) or np.all(ln == bg):
            continue
        slots.append(i)
    # Visit the slots in the visible direction that corresponds to the
    # original left-to-right order. The most-holed slot goes to the first one.
    if REVERSE:
        slots = slots[::-1]
    contents = [_line(g, i) for i in slots]
    holes = [int(np.sum(c == HOLE)) for c in contents]
    order = sorted(range(len(slots)), key=lambda j: -holes[j])
    out = g.copy()
    for pos, j in enumerate(order):
        _put(out, slots[pos], contents[j])
    return out.tolist()
''' % (hole, slots_are_columns, reverse)
    return src

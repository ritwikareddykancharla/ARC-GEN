def build_program(d4, palette):
    bg = int(palette[0])
    shape = int(palette[8])
    # Canonical scan direction: along columns, left to right, so the displacement is (dr, dc) = (0, +1).
    dr, dc = 0, 1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        # A clockwise rotation maps old (r, c) to new (c, H-1-r), so a displacement (dr, dc) becomes (dc, -dr).
        dr, dc = dc, -dr
    if dr != 0:
        axis = 0
        step = 1 if dr > 0 else -1
    else:
        axis = 1
        step = 1 if dc > 0 else -1
    template = '''import numpy as np

BG = __BG__
SHAPE = __SHAPE__
AXIS = __AXIS__   # 0: slices are rows (scan moves vertically); 1: slices are columns (scan moves horizontally)
STEP = __STEP__   # +1: scan toward increasing index; -1: scan toward decreasing index


def _slice(a, i):
    return a[i, :] if AXIS == 0 else a[:, i]


def _set_line(a, i, v):
    if AXIS == 0:
        a[i, :] = v
    else:
        a[:, i] = v


def _set_cell(a, i, p, v):
    if AXIS == 0:
        a[i, p] = v
    else:
        a[p, i] = v


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    n = g.shape[AXIS]
    order = list(range(n)) if STEP > 0 else list(range(n - 1, -1, -1))
    # Legend: full-length uniform lines that are neither background nor the shape colour.
    # Read them in scan order and erase them.
    legend = []
    for i in order:
        line = _slice(g, i)
        v = int(line[0])
        if v != BG and v != SHAPE and bool(np.all(line == v)):
            legend.append(v)
            _set_line(out, i, BG)
    # Shape rectangles: a maximal run of consecutive slices (in scan order) whose
    # shape-colour cell positions are identical. Any change of that set, or an
    # empty slice, starts a new rectangle.
    blocks = []
    prev = None
    for i in order:
        pos = tuple(int(p) for p in np.nonzero(_slice(g, i) == SHAPE)[0])
        if not pos:
            prev = None
            continue
        if prev is not None and pos == prev:
            blocks[-1][0].append(i)
        else:
            blocks.append(([i], pos))
        prev = pos
    # The k-th rectangle in scan order takes the k-th legend colour.
    for k, (idxs, pos) in enumerate(blocks):
        if k >= len(legend):
            break
        c = legend[k]
        for i in idxs:
            for p in pos:
                _set_cell(out, i, p, c)
    return out.tolist()
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__SHAPE__', str(shape))
                    .replace('__AXIS__', str(axis))
                    .replace('__STEP__', str(step)))

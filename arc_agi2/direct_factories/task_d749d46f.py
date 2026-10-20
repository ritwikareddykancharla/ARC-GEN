TEMPLATE = '''import numpy as np

# Orientation constants chosen by the factory for this D4 view.
# HORIZ: the boxes form a sequence along the columns, so they hang from the top or bottom edge.
#        If False, the sequence runs along the rows and the boxes hang from the left or right edge.
# HANG_LOW: the hanging edge is at index 0 of the perpendicular axis (the top or left edge).
# SEQ_FWD: the left-to-right order starts at index 0 of the sequence axis (the left or top end).
HORIZ = @H@
HANG_LOW = @L@
SEQ_FWD = @S@
DEPTH = 10


def _lines(g):
    out = []
    if HORIZ:
        n = g.shape[1]
        order = range(n) if SEQ_FWD else range(n - 1, -1, -1)
        for x in order:
            line = g[:, x]
            out.append(line if HANG_LOW else line[::-1])
    else:
        n = g.shape[0]
        order = range(n) if SEQ_FWD else range(n - 1, -1, -1)
        for y in order:
            line = g[y, :]
            out.append(line if HANG_LOW else line[::-1])
    return out


def _boxes(g):
    lines = _lines(g)
    fg = int(lines[0][0])
    depths = []
    for line in lines:
        d = 0
        while d < len(line) and int(line[d]) == fg:
            d += 1
        depths.append(d)
    boxes = []
    i = 0
    n = len(depths)
    while i < n:
        if depths[i] > 0:
            j = i
            dmax = 0
            while j < n and depths[j] > 0:
                dmax = max(dmax, depths[j])
                j += 1
            boxes.append((j - i, dmax))
            i = j
        else:
            i += 1
    return fg, boxes


def _paint(out, L, D, s0, slen, p0, plen, colour):
    for s in range(s0, s0 + slen):
        sv = s if SEQ_FWD else L - 1 - s
        for p in range(p0, p0 + plen):
            pv = p if HANG_LOW else D - 1 - p
            if HORIZ:
                out[pv, sv] = colour
            else:
                out[sv, pv] = colour


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    fg, boxes = _boxes(g)
    vals, counts = np.unique(g, return_counts=True)
    others = [(int(c), int(v)) for v, c in zip(vals, counts) if int(v) != fg]
    bg = max(others)[1] if others else fg
    dims = [(min(a, b), max(a, b)) for a, b in boxes]
    if not dims:
        return g.tolist()
    L = sum(l for _, l in dims) + len(dims) - 1
    D = max(DEPTH, max(l for _, l in dims))
    out = np.full((D, L) if HORIZ else (L, D), bg, dtype=int)
    pos = 0
    for s, l in dims:
        _paint(out, L, D, pos, l, 0, s, fg)
        pos += l + 1
    pos = 0
    for s, l in dims:
        _paint(out, L, D, pos, s, D - l, l, fg)
        pos += s + 1
    return out.tolist()
'''


def build_program(d4, palette):
    k = int(d4) % 4
    flip = int(d4) >= 4
    table = {
        (False, 0): (True, True, True),
        (False, 1): (False, False, True),
        (False, 2): (True, False, False),
        (False, 3): (False, True, False),
        (True, 0): (True, True, False),
        (True, 1): (False, False, False),
        (True, 2): (True, False, True),
        (True, 3): (False, True, True),
    }
    horiz, hang_low, seq_fwd = table[(flip, k)]
    return (TEMPLATE.replace('@H@', repr(horiz))
                    .replace('@L@', repr(hang_low))
                    .replace('@S@', repr(seq_fwd)))

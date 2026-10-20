_TEMPLATE = '''import numpy as np
from collections import Counter

# Specialised for the visible orientation of this episode.
# True: each mirror line is a grid column, so a cell (y, x) pairs with (y, s - x).
# False: each mirror line is a grid row, so a cell (y, x) pairs with (s - y, x).
MIRROR_ACROSS_COLUMNS = @ACROSS@
# Tie-break between equally good axes.
# True: the smallest doubled axis s wins. False: the largest wins.
PREFER_LOW = @LOW@


def _background(g):
    return int(Counter(g.ravel().tolist()).most_common(1)[0][0])


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = _background(g)
    out = g.copy()
    colours = sorted(int(c) for c in np.unique(g) if int(c) != bg)
    for col in colours:
        ys, xs = np.nonzero(g == col)
        cells = set(zip(ys.tolist(), xs.tolist()))
        if not cells:
            continue
        coord = xs.tolist() if MIRROR_ACROSS_COLUMNS else ys.tolist()
        lo, hi = 2 * min(coord), 2 * max(coord)
        order = range(lo, hi + 1) if PREFER_LOW else range(hi, lo - 1, -1)
        best = None
        for s in order:
            if MIRROR_ACROSS_COLUMNS:
                keep = {(y, x) for (y, x) in cells if (y, s - x) in cells}
            else:
                keep = {(y, x) for (y, x) in cells if (s - y, x) in cells}
            if best is None or len(keep) > len(best):
                best = keep
        for (y, x) in cells - best:
            out[y, x] = bg
    return out.tolist()
'''


def build_program(d4, palette):
    k = int(d4) % 8
    r = k % 4
    flip = k >= 4
    # In the original task, each mirror line is a column (a left-right mirror).
    # A quarter turn makes the line a row.
    across_columns = r in (0, 2)
    # In the original task, ties go to the axis with the smallest x.
    # Track where increasing original x points in the visible grid:
    #   r=0 right (columns grow), r=1 down (rows grow),
    #   r=2 left (columns shrink), r=3 up (rows shrink).
    # The row reversal for d4 >= 4 flips that direction.
    prefer_low = (r in (0, 1)) != flip
    return (_TEMPLATE
            .replace('@ACROSS@', repr(bool(across_columns)))
            .replace('@LOW@', repr(bool(prefer_low))))

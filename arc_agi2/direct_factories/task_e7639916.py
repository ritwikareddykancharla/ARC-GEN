def build_program(d4, palette):
    bg = int(palette[0])
    line = int(palette[1])
    marker = int(palette[8])
    src = '''import numpy as np

BG = %d
LINE = %d
MARKER = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    mask = (g == MARKER)
    if not mask.any():
        mask = (g != BG)
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return out.tolist()
    r0, r1 = int(ys.min()), int(ys.max())
    c0, c1 = int(xs.min()), int(xs.max())
    # top and bottom edges
    for c in range(c0, c1 + 1):
        for r in (r0, r1):
            if out[r, c] == BG:
                out[r, c] = LINE
    # left and right edges
    for r in range(r0, r1 + 1):
        for c in (c0, c1):
            if out[r, c] == BG:
                out[r, c] = LINE
    return out.tolist()
''' % (bg, line, marker)
    return src

def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    blue = int(palette[1])
    src = '''import numpy as np

BG = %d
RED = %d
BLUE = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    mask = g != BG
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return out.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    gap_rows = [y for y in range(y0, y1 + 1) if not mask[y, x0:x1 + 1].any()]
    gap_cols = [x for x in range(x0, x1 + 1) if not mask[y0:y1 + 1, x].any()]
    for y in gap_rows:
        out[y, x0:x1 + 1] = RED
    for x in gap_cols:
        out[y0:y1 + 1, x] = RED
    for y in gap_rows:
        out[y, :x0] = BLUE
        out[y, x1 + 1:] = BLUE
    for x in gap_cols:
        out[:y0, x] = BLUE
        out[y1 + 1:, x] = BLUE
    return out.tolist()
''' % (bg, red, blue)
    return src

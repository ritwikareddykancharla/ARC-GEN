def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[2])
    # The original input stacks two equal halves vertically (rows 0..s-1 and s..2s-1).
    # An odd number of clockwise quarter turns makes the stacking horizontal.
    # A row reversal before rotating does not change which axis the halves are stacked on.
    axis = 1 if (d4 % 4) in (1, 3) else 0
    src = '''import numpy as np

BG = %d
MARK = %d
AXIS = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    axis = AXIS
    # Safety net: prefer the long dimension if the shape clearly disagrees.
    if axis == 0 and w > h:
        axis = 1
    elif axis == 1 and h > w:
        axis = 0
    if axis == 0:
        s = h // 2
        a = g[:s, :]
        b = g[s:2 * s, :]
    else:
        s = w // 2
        a = g[:, :s]
        b = g[:, s:2 * s]
    out = np.full(a.shape, BG, dtype=int)
    # Mark the cells that are empty (background) in both halves.
    out[(a == BG) & (b == BG)] = MARK
    return out.tolist()
''' % (bg, mark, axis)
    return src

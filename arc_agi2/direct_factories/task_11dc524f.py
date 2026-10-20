def build_program(d4, palette):
    two = int(palette[2])
    five = int(palette[5])
    bg = int(palette[7])
    src = '''import numpy as np

TWO = %d
FIVE = %d
BG = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    tys, txs = np.where(g == TWO)
    fys, fxs = np.where(g == FIVE)
    if len(tys) == 0 or len(fys) == 0:
        return g.tolist()
    two = [(int(y), int(x)) for y, x in zip(tys, txs)]
    ty0, ty1 = int(tys.min()), int(tys.max())
    tx0, tx1 = int(txs.min()), int(txs.max())
    fy0, fy1 = int(fys.min()), int(fys.max())
    fx0, fx1 = int(fxs.min()), int(fxs.max())
    out = g.copy()
    out[g == TWO] = BG
    out[g == FIVE] = BG
    # Empty gap between the two bounding boxes along each visible axis.
    # The axis carrying the real separation is the axis of motion.
    row_gap = max(fy0 - ty1, ty0 - fy1) - 1
    col_gap = max(fx0 - tx1, tx0 - fx1) - 1
    if col_gap > row_gap:
        # Horizontal approach: slide sideways until the boxes touch.
        if tx1 < fx0:
            dy, dx = 0, fx0 - 1 - tx1
            line2 = 2 * fx0 - 1
        else:
            dy, dx = 0, fx1 + 1 - tx0
            line2 = 2 * fx1 + 1
        mirror = lambda y, x: (y, line2 - x)
    else:
        # Vertical approach.
        if ty1 < fy0:
            dy, dx = fy0 - 1 - ty1, 0
            line2 = 2 * fy0 - 1
        else:
            dy, dx = fy1 + 1 - ty0, 0
            line2 = 2 * fy1 + 1
        mirror = lambda y, x: (line2 - y, x)
    moved = [(y + dy, x + dx) for y, x in two]
    for y, x in moved:
        if 0 <= y < H and 0 <= x < W:
            out[y, x] = TWO
    for y, x in moved:
        my, mx = mirror(y, x)
        if 0 <= my < H and 0 <= mx < W:
            out[my, mx] = FIVE
    return out.tolist()
''' % (two, five, bg)
    return src

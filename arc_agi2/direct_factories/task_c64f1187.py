def build_program(d4, palette):
    # Direction from a legend marker to its 2x2 shape window in the ORIGINAL frame is (+1,+1).
    # Transform that displacement: a horizontal flip negates the column component, and each
    # clockwise rotation maps (dr, dc) -> (dc, -dr).
    dr, dc = 1, 1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    # Offset from the marker to the visible top-left of the window that spans marker+{1,2}*dir.
    wy = 1 if dr > 0 else -2
    wx = 1 if dc > 0 else -2
    bg = int(palette[0])
    one = int(palette[1])
    five = int(palette[5])
    src = '''import numpy as np

BG = %d
ONE = %d
FIVE = %d
WY = %d
WX = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    ys, xs = np.where(g == FIVE)
    if ys.size == 0:
        return [[BG]]
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    # Legend: every marker colour outside the block canvas owns the 2x2 window of ONE-cells
    # lying diagonally away from it (direction fixed by the visible orientation).
    shapes = {}
    for y in range(H):
        for x in range(W):
            c = int(g[y, x])
            if c in (BG, ONE, FIVE):
                continue
            if y0 <= y <= y1 and x0 <= x <= x1:
                continue
            ty, tx = y + WY, x + WX
            if ty < 0 or tx < 0 or ty + 2 > H or tx + 2 > W:
                continue
            win = g[ty:ty + 2, tx:tx + 2] == ONE
            if win.any():
                shapes[c] = win
    # Canvas: crop to the FIVE bounding box, clear it, and stamp each tagged block.
    oh, ow = y1 - y0 + 1, x1 - x0 + 1
    out = np.full((oh, ow), BG, dtype=int)
    for by in range(0, oh, 3):
        for bx in range(0, ow, 3):
            blk = g[y0 + by:y0 + by + 2, x0 + bx:x0 + bx + 2]
            cols = [int(v) for v in blk.flatten() if int(v) not in (BG, FIVE)]
            if not cols:
                continue
            c = cols[0]
            if c not in shapes:
                continue
            mask = shapes[c]
            sub = out[by:by + 2, bx:bx + 2]
            m = mask[:sub.shape[0], :sub.shape[1]]
            sub[m] = c
    return [[int(v) for v in row] for row in out]
''' % (bg, one, five, wy, wx)
    return src

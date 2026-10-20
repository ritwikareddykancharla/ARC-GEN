def build_program(d4, palette):
    d4 = int(d4) % 8
    # Canonical directions: DOWN runs along the bar, away from its anchoring edge.
    # LEFT is the side that receives colour 8 (azure).
    down = (1, 0)
    left = (0, -1)
    if d4 >= 4:
        # Reversing each row negates the column component of a direction.
        down = (down[0], -down[1])
        left = (left[0], -left[1])
    for _ in range(d4 % 4):
        # A clockwise rotation maps direction (dr, dc) to (dc, -dr).
        down = (down[1], -down[0])
        left = (left[1], -left[0])
    bg = int(palette[0])
    bar = int(palette[5])
    left_col = int(palette[8])
    right_col = int(palette[6])
    src = '''import numpy as np

BG = %d
BAR = %d
LEFT_COL = %d
RIGHT_COL = %d
DOWN = (%d, %d)
LEFT = (%d, %d)

def _along(y, x, H, W):
    # Distance from the anchoring edge, measured along DOWN.
    if DOWN == (1, 0):
        return y
    if DOWN == (-1, 0):
        return H - 1 - y
    if DOWN == (0, 1):
        return x
    return W - 1 - x

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    ys, xs = np.where(g == BAR)
    if len(ys) == 0:
        ys, xs = np.where(g != BG)
        if len(ys) == 0:
            return g.tolist()
    by, bx = int(ys[0]), int(xs[0])
    alongs = [_along(int(y), int(x), H, W) for y, x in zip(ys, xs)]
    start = min(alongs)
    L = max(alongs) - start + 1
    out = g.copy()
    for y in range(H):
        for x in range(W):
            k = (y - by) * LEFT[0] + (x - bx) * LEFT[1]
            if k == 0:
                continue
            a = _along(y, x, H, W) - start
            # Fill a cell if a >= 0 and a < L + 2*k.
            # On the azure side k = d > 0, so the strip is L + 2d long.
            # On the magenta side k = -d, so the strip is L - 2d long.
            if 0 <= a < L + 2 * k:
                out[y, x] = LEFT_COL if k > 0 else RIGHT_COL
    return out.tolist()
''' % (bg, bar, left_col, right_col, down[0], down[1], left[0], left[1])
    return src

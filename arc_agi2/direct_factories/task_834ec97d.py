def build_program(d4, palette):
    # Original mechanism: the pixel moves one step DOWN, i.e. along (+1, 0).
    # Row reversal (d4 >= 4) only negates column offsets, so it leaves (+1, 0) unchanged.
    # A clockwise rotation maps a cell offset (dr, dc) to (dc, -dr).
    dr, dc = 1, 0
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    bg = int(palette[0])
    yellow = int(palette[4])
    src = '''import numpy as np

DR = %d
DC = %d
BG = %d
STRIPE = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.nonzero(g != BG)
    if len(ys) == 0:
        return out.tolist()
    r, c = int(ys[0]), int(xs[0])
    colour = int(g[r, c])
    if DR != 0:
        # The motion is vertical in the visible grid.
        # Stripes run along columns that share the pixel's column parity.
        # They cover the pixel's row and every row behind it (opposite to the motion).
        for y in range(H):
            if (y - r) * DR > 0:
                continue
            for x in range(W):
                if (x - c) %% 2 == 0:
                    out[y, x] = STRIPE
    else:
        # The motion is horizontal in the visible grid.
        # Stripes run along rows that share the pixel's row parity.
        # They cover the pixel's column and every column behind it.
        for x in range(W):
            if (x - c) * DC > 0:
                continue
            for y in range(H):
                if (y - r) %% 2 == 0:
                    out[y, x] = STRIPE
    ny, nx = r + DR, c + DC
    if 0 <= ny < H and 0 <= nx < W:
        out[ny, nx] = colour
    return out.tolist()
''' % (dr, dc, bg, yellow)
    return src

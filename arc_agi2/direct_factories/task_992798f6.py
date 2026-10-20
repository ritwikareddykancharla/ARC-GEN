def build_program(d4, palette):
    c_bg = int(palette[0])
    c_start = int(palette[1])
    c_goal = int(palette[2])
    c_path = int(palette[3])
    src = '''import numpy as np

START = %d
GOAL = %d
PATH = %d
BG = %d

def _sign(v):
    return (v > 0) - (v < 0)

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    a = np.argwhere(g == START)
    b = np.argwhere(g == GOAL)
    if len(a) == 0 or len(b) == 0:
        return g.tolist()
    y, x = int(a[0][0]), int(a[0][1])
    gy, gx = int(b[0][0]), int(b[0][1])
    sy = _sign(gy - y)
    sx = _sign(gx - x)
    # T: the cell diagonally touching the goal, on the side facing the start
    ty, tx = gy - sy, gx - sx
    if sy == 0 or sx == 0:
        # Degenerate (outside constructor domain): straight line to the cell before the goal
        while (y, x) != (ty, tx):
            y += sy
            x += sx
            if (y, x) == (gy, gx):
                break
            g[y, x] = PATH
        return g.tolist()
    H, W = g.shape
    # Diagonal leg: step toward the goal until T's row or T's column is reached
    while y != ty and x != tx:
        y += sy
        x += sx
        if 0 <= y < H and 0 <= x < W:
            g[y, x] = PATH
    # Straight leg along whichever axis still differs, ending on T
    while (y, x) != (ty, tx):
        if y != ty:
            y += sy
        if x != tx:
            x += sx
        if 0 <= y < H and 0 <= x < W:
            g[y, x] = PATH
    return g.tolist()
''' % (c_start, c_goal, c_path, c_bg)
    return src

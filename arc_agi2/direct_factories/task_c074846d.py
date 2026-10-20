def build_program(d4, palette):
    red = int(palette[2])
    grey = int(palette[5])
    green = int(palette[3])
    reflected = int(d4) >= 4
    # Original rule: arm turns clockwise, (dy,dx)->(dx,-dy).
    # Pure rotations commute with a quarter turn, so the arm still turns clockwise.
    # A reflection reverses handedness, so the visible turn becomes counter-clockwise, (dy,dx)->(-dx,dy).
    if reflected:
        turn_expr = "(-dx, dy)"
    else:
        turn_expr = "(dx, -dy)"
    src = '''import numpy as np

RED = %d
GREY = %d
GREEN = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    pivots = np.argwhere(g == GREY)
    reds = [(int(y), int(x)) for y, x in np.argwhere(g == RED)]
    if len(pivots) == 0 or len(reds) == 0:
        return out.tolist()
    py, px = int(pivots[0][0]), int(pivots[0][1])
    n = len(reds)
    sy = sum(y - py for y, _ in reds)
    sx = sum(x - px for _, x in reds)
    dy = int(np.sign(sy))
    dx = int(np.sign(sx))
    for y, x in reds:
        out[y, x] = GREEN
    ndy, ndx = %s
    for k in range(1, n + 1):
        y, x = py + ndy * k, px + ndx * k
        if 0 <= y < H and 0 <= x < W:
            out[y, x] = RED
    return out.tolist()
''' % (red, grey, green, turn_expr)
    return src

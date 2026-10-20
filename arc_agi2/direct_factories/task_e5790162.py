def build_program(d4, palette):
    k = d4 % 4
    refl = d4 >= 4
    # Canonical start heading: rightward (dr, dc) = (0, 1).
    dr, dc = 0, 1
    if refl:
        dc = -dc
    for _ in range(k):
        # Clockwise grid rotation maps direction (dr, dc) -> (dc, -dr).
        dr, dc = dc, -dr
    bg = palette[0]
    green = palette[3]
    cw_col = palette[6]
    ccw_col = palette[8]
    if refl:
        # A reflection reverses the handedness of the turns.
        cw_col, ccw_col = ccw_col, cw_col
    src = '''import numpy as np

BG = %d
GREEN = %d
CW_COL = %d
CCW_COL = %d
START_DR = %d
START_DC = %d

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    start = None
    for r in range(H):
        for c in range(W):
            if g[r][c] == GREEN:
                start = (r, c)
                break
        if start is not None:
            break
    if start is None:
        return g
    y, x = start
    dy, dx = START_DR, START_DC
    steps = 0
    limit = H * W * 4 + 8
    while steps < limit:
        steps += 1
        ny, nx = y + dy, x + dx
        if not (0 <= ny < H and 0 <= nx < W):
            break
        v = g[ny][nx]
        if v != BG and v != GREEN:
            if v == CCW_COL:
                # counter-clockwise on screen
                dy, dx = -dx, dy
            else:
                # clockwise on screen (CW_COL and any unknown obstacle)
                dy, dx = dx, -dy
            continue
        y, x = ny, nx
        g[y][x] = GREEN
    return g
''' % (bg, green, cw_col, ccw_col, dr, dc)
    return src

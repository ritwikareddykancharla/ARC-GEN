def build_program(d4, palette):
    # Original mechanism: the path moves forward from the seed. A colour-3 cell ahead
    # makes it side-step clockwise; a colour-1 cell ahead makes it side-step
    # counter-clockwise. Rotations keep this handedness. Reflections (d4>=4) swap it.
    if d4 % 8 < 4:
        cw_col, ccw_col = palette[3], palette[1]
    else:
        cw_col, ccw_col = palette[1], palette[3]
    seed_col = palette[2]
    src = '''
CW_COL = %d
CCW_COL = %d
SEED = %d

def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [r[:] for r in g]
    seeds = [(r, c) for r in range(H) for c in range(W) if g[r][c] == SEED]
    if not seeds:
        return out
    border = [p for p in seeds if p[0] in (0, H - 1) or p[1] in (0, W - 1)]
    y, x = (border or seeds)[0]
    # Head inward, away from the border that holds the seed.
    if x == 0 and W > 1:
        d = (0, 1)
    elif x == W - 1 and W > 1:
        d = (0, -1)
    elif y == 0:
        d = (1, 0)
    else:
        d = (-1, 0)
    cw = (d[1], -d[0])
    ccw = (-d[1], d[0])
    steps = 0
    limit = 4 * H * W + 10
    while steps < limit:
        steps += 1
        out[y][x] = SEED
        ny, nx = y + d[0], x + d[1]
        if not (0 <= ny < H and 0 <= nx < W):
            break
        c = g[ny][nx]
        if c == CW_COL:
            y, x = y + cw[0], x + cw[1]
        elif c == CCW_COL:
            y, x = y + ccw[0], x + ccw[1]
        else:
            y, x = ny, nx
        if not (0 <= y < H and 0 <= x < W):
            break
    return out
''' % (cw_col, ccw_col, seed_col)
    return src

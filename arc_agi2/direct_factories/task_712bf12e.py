def build_program(d4, palette):
    d4 = int(d4) % 8

    def tf(dr, dc):
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc

    ur, uc = tf(-1, 0)   # original 'up' (growth direction)
    rr, rc = tf(0, 1)    # original 'right' (sidestep direction)
    bg = int(palette[0])
    obst = int(palette[5])
    seed = int(palette[2])

    src = '''
UR, UC = %d, %d
RR, RC = %d, %d
BG = %d
OBST = %d
SEED = %d


def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0

    def inside(y, x):
        return 0 <= y < H and 0 <= x < W

    # Seeds sit on the edge opposite the growth direction:
    # stepping one cell against the growth direction leaves the grid.
    seeds = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == SEED and not inside(y - UR, x - UC):
                seeds.append((y, x))
    # Process seeds in order along the sidestep axis.
    seeds.sort(key=lambda p: p[0] * RR + p[1] * RC)

    for sy, sx in seeds:
        y, x = sy, sx
        while True:
            ny, nx = y + UR, x + UC
            if not inside(ny, nx):
                break  # reached the far edge
            if g[ny][nx] == OBST:
                ry, rx = y + RR, x + RC
                if not inside(ry, rx) or g[ry][rx] == OBST:
                    break  # sidestep blocked or off-grid
                y, x = ry, rx
            else:
                y, x = ny, nx
            g[y][x] = SEED
    return g
''' % (ur, uc, rr, rc, bg, obst, seed)
    return src

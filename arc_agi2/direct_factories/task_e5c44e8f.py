def build_program(d4, palette):
    d4 = int(d4) % 8
    green = int(palette[3])
    red = int(palette[2])

    def tdir(dr, dc):
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)

    base = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dirs = [tdir(a, b) for a, b in base]

    src = '''import numpy as np

GREEN = %d
RED = %d
DIRS = %r


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    pos = np.argwhere(g == GREEN)
    if len(pos) == 0:
        return out.tolist()
    y, x = int(pos[0][0]), int(pos[0][1])
    length = 2
    seg = 0
    limit = 4 * (H + W) + 8
    stopped = False
    while not stopped and seg < limit:
        dy, dx = DIRS[seg %% 4]
        for _ in range(length):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and g[ny, nx] == RED:
                stopped = True
                break
            y, x = ny, nx
            if 0 <= y < H and 0 <= x < W:
                out[y, x] = GREEN
        seg += 1
        if seg %% 2 == 0:
            length += 2
    return out.tolist()
''' % (green, red, dirs)
    return src

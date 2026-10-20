def build_program(d4, palette):
    d4 = int(d4) % 8

    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (int(dr), int(dc))

    along = tf((0, 1))
    up = tf((-1, 0))
    bar = int(palette[2])
    up_c = int(palette[3])
    down_c = int(palette[1])

    src = '''import numpy as np

BAR = %d
UP_COLOUR = %d
DOWN_COLOUR = %d
ALONG = (%d, %d)
UP = (%d, %d)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    cells = np.argwhere(g == BAR)
    if len(cells) == 0:
        return out.tolist()
    proj = cells[:, 0] * ALONG[0] + cells[:, 1] * ALONG[1]
    i = int(np.argmin(proj))
    ar, ac = int(cells[i][0]), int(cells[i][1])
    L = int(proj.max() - proj.min() + 1)

    def inside(r, c):
        return 0 <= r < H and 0 <= c < W

    def draw_run(r0, c0, n, colour):
        for j in range(n):
            r = r0 + j * ALONG[0]
            c = c0 + j * ALONG[1]
            if not inside(r, c):
                break
            out[r, c] = colour

    # widening staircase on the 'up' side of the bar, out to the grid edge
    k = 1
    while True:
        r0 = ar + k * UP[0]
        c0 = ac + k * UP[1]
        if not inside(r0, c0):
            break
        draw_run(r0, c0, L + k, UP_COLOUR)
        k += 1

    # shrinking staircase on the opposite side, until length reaches 0
    for k in range(1, L):
        r0 = ar - k * UP[0]
        c0 = ac - k * UP[1]
        if not inside(r0, c0):
            break
        draw_run(r0, c0, L - k, DOWN_COLOUR)

    return out.tolist()
''' % (bar, up_c, down_c, along[0], along[1], up[0], up[1])
    return src
